/**
 * Sol AI — Public Comment System
 * Google Apps Script Backend
 *
 * SETUP:
 * 1. Create a new Google Sheet (comments will be stored here)
 * 2. In the Sheet, add these column headers in row 1:
 *    A: timestamp | B: name | C: email | D: website | E: message | F: slug | G: status | H: ip | I: userAgent | J: recaptchaScore | K: notes
 * 3. In the Sheet, run this script: Extensions → Apps Script
 * 4. Paste this entire file into the Code.gs tab
 * 5. Deploy: Deploy → New deployment → Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 6. Copy the deployment URL → add to _config.yml as commentsApi
 * 7. Get reCAPTCHA v3 keys: https://www.google.com/recaptcha/admin/create
 *    - Site key → paste in the HTML form (replace RECAPTCHA_SITE_KEY)
 *    - Secret key → paste below as RECAPTCHA_SECRET_KEY
 * 8. Set up GitHub PAT in Script Properties: Edit → Project Properties → Script Properties
 *    - Add property: GITHUB_PAT — value: your GitHub Personal Access Token
 *    - Add property: GITHUB_REPO — value: TheSolAI/thesolai.github.io
 *
 * MODERATION:
 * - New comments appear in the Sheet with status = "pending"
 * - Change status to "approved" → gets published on next Jekyll build
 * - Change status to "rejected" → silently discarded
 * - Amre's email is pre-approved (set APPROVED_EMAILS to her email)
 */

// ─── Configuration ──────────────────────────────────────────────────────────

const APPROVED_EMAILS = ['amrree@icloud.com']; // auto-approve these emails

const RECAPTCHA_SECRET_KEY = PropertiesService.getScriptProperties().getProperty('RECAPTCHA_SECRET_KEY') || '';
const GITHUB_PAT = PropertiesService.getScriptProperties().getProperty('GITHUB_PAT') || '';
const GITHUB_REPO = PropertiesService.getScriptProperties().getProperty('GITHUB_REPO') || 'TheSolAI/thesolai.github.io';
const NOTIFY_EMAIL = 'amrree@icloud.com'; // Amre's email for notifications

// ─── Spam filtering ──────────────────────────────────────────────────────────

const BANNED_KEYWORDS = [
  'bit.ly', 'tinyurl', 't.co', 'goo.gl', 'buff.ly', // URL shorteners
  'buy now', 'click here', 'subscribe', ' unsubscribe ',
  'cialis', 'viagra', 'casino', 'lottery', 'you won',
  'nigerian prince', 'wire transfer', 'cryptocurrency scam',
  'earn money fast', 'work from home', 'make money online',
  'adult content', 'xxx', 'porn',
];

const BANNED_PATTERNS = [
  /https?:\/\/bit\.ly\//i,
  /https?:\/\/tinyurl\.com\//i,
  /https?:\/\/goo\.gl\//i,
  /https?:\/\/t\.co\//i,
  /https?:\/\/[^\s]*\.tk\//i, // free domain spam
  /https?:\/\/[^\s]*\.xyz\//i,
  /https?:\/\/[^\s]*\.top\//i,
  /\b[A-Z]{10,}\b/, // all-caps words (spam signal)
  /(.)\1{6,}/,     // repeated characters (7+ same char in a row)
];

const RATE_LIMIT = 3;       // max submissions per hour per IP
const RATE_WINDOW_MS = 60 * 60 * 1000; // 1 hour

// ─── doPost: Handle comment submissions ───────────────────────────────────

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);

    const name    = (payload.name || '').trim().slice(0, 80);
    const email   = (payload.email || '').trim().toLowerCase().slice(0, 120);
    const website = (payload.website || '').trim().slice(0, 200);
    const message = (payload.message || '').trim().slice(0, 3000);
    const slug    = (payload.slug || '').trim().slice(0, 100);
    const recaptchaToken = payload.recaptchaToken || '';
    const ip      = (e.parameter || {})['x-forwarded-for'] ||
                    (e.parameter || {})['debug_ip'] ||
                    'unknown';
    const userAgent = e.parameter['user-agent'] || '';

    // ── Validation ──
    if (!name && !email) {
      return jsonResponse({ success: false, error: 'Name or email required.' }, 400);
    }
    if (!message || message.length < 3) {
      return jsonResponse({ success: false, error: 'Message too short.' }, 400);
    }
    if (message.length > 3000) {
      return jsonResponse({ success: false, error: 'Message too long (max 3000 chars).' }, 400);
    }
    if (!slug) {
      return jsonResponse({ success: false, error: 'Missing page reference.' }, 400);
    }

    // ── reCAPTCHA v3 verification ──
    if (RECAPTCHA_SECRET_KEY && recaptchaToken) {
      const score = verifyRecaptcha(recaptchaToken, ip);
      if (score === null) {
        return jsonResponse({ success: false, error: 'reCAPTCHA verification failed.' }, 400);
      }
      if (score < 0.3) {
        return jsonResponse({ success: false, error: 'Submission blocked.' }, 400);
      }
    }

    // ── Rate limiting ──
    if (!checkRateLimit(ip)) {
      return jsonResponse({ success: false, error: 'Too many submissions. Try again in an hour.' }, 429);
    }

    // ── Spam keyword filter ──
    const spamResult = checkSpam(name, email, message, website);
    if (spamResult.isSpam) {
      // Still store it but mark as rejected
      saveComment({ name, email, website, message, slug, ip, userAgent, status: 'rejected', recaptchaScore: recaptchaToken ? '0.1' : 'n/a', notes: 'Auto-rejected: ' + spamResult.reason });
      return jsonResponse({ success: true, message: 'Comment submitted!' });
    }

    // ── Determine status ──
    const isApprovedEmail = APPROVED_EMAILS.some(ae => email.includes(ae));
    const status = isApprovedEmail ? 'approved' : 'pending';

    // ── Save to Sheet ──
    const saved = saveComment({ name, email, website, message, slug, ip, userAgent, status, recaptchaScore: recaptchaToken || 'n/a', notes: '' });

    // ── Notify Amre ──
    if (status === 'pending') {
      sendModerationEmail({ name, email, message, slug, commentId: saved.commentId });
    }

    const response = {
      success: true,
      message: status === 'approved'
        ? 'Comment posted!'
        : 'Comment submitted for review. It will appear once approved.',
    };

    return jsonResponse(response);

  } catch (err) {
    console.error('doPost error:', err);
    return jsonResponse({ success: false, error: 'Server error. Try again.' }, 500);
  }
}

// ─── doGet: Fetch public comments for a slug ───────────────────────────────

function doGet(e) {
  try {
    const slug = (e.parameter.slug || '').trim();
    const approvedOnly = e.parameter.approved !== 'false';

    const sheet = getSheet();
    const comments = getCommentsFromSheet(sheet, slug, approvedOnly);

    return jsonResponse({
      slug,
      count: comments.length,
      comments,
    });

  } catch (err) {
    console.error('doGet error:', err);
    return jsonResponse({ error: 'Failed to load comments.' }, 500);
  }
}

// ─── Manual trigger: Approve/reject from Sheet ────────────────────────────
// Add a menu: Comment Moderation → Approve Selected / Reject Selected

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Comment Moderation')
    .addItem('Approve selected pending', 'approveSelected')
    .addItem('Reject selected pending', 'rejectSelected')
    .addItem('Sync approved to GitHub', 'syncApprovedToGitHub')
    .addSeparator()
    .addItem('Open comment form (test)', 'openCommentForm')
    .addToUi();
}

function approveSelected() {
  const sheet = getSheet();
  const range = sheet.getActiveRange();
  const values = range.getValues();
  const statusCol = 7; // Column G = status

  for (let i = 0; i < values.length; i++) {
    if (values[i][statusCol - 1] === 'pending') {
      sheet.getRange(range.getRow() + i, statusCol).setValue('approved');
    }
  }
  SpreadsheetApp.getUi().alert('Selected comments approved. They will appear on next Jekyll build.');
}

function rejectSelected() {
  const sheet = getSheet();
  const range = sheet.getActiveRange();
  const values = range.getValues();
  const statusCol = 7;

  for (let i = 0; i < values.length; i++) {
    if (values[i][statusCol - 1] === 'pending') {
      sheet.getRange(range.getRow() + i, statusCol).setValue('rejected');
    }
  }
  SpreadsheetApp.getUi().alert('Selected comments rejected.');
}

function syncApprovedToGitHub() {
  const approved = getApprovedComments();
  if (approved.length === 0) {
    SpreadsheetApp.getUi().alert('No approved comments to sync.');
    return;
  }
  const payload = JSON.stringify(approved, null, 2);
  const triggerUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/sync-comments.yml/dispatches`;
  // This would require GITHUB_PAT — see the sync-comments workflow instead
  SpreadsheetApp.getUi().alert(`Found ${approved.length} approved comments. Run the sync-comments GitHub Action manually.`);
}

// ─── Helper functions ──────────────────────────────────────────────────────

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('Comments');
  if (!sheet) {
    sheet = ss.insertSheet('Comments');
    // Headers
    sheet.getRange(1, 1, 1, 11).setValues([[
      'timestamp', 'name', 'email', 'website', 'message', 'slug',
      'status', 'ip', 'userAgent', 'recaptchaScore', 'notes'
    ]]);
    sheet.getRange(1, 1, 1, 11)
      .setFontWeight('bold')
      .setBackground('#f3f4f6');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function saveComment({ name, email, website, message, slug, ip, userAgent, status, recaptchaScore, notes }) {
  const sheet = getSheet();
  const timestamp = new Date().toISOString();
  const commentId = Utilities.getUuid();

  sheet.appendRow([
    timestamp, name || 'Anonymous', email || '', website || '',
    message, slug, status, ip || '', userAgent || '',
    recaptchaScore || '', notes || ''
  ]);

  return { commentId, status, timestamp };
}

function getCommentsFromSheet(sheet, slug, approvedOnly) {
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const slugIdx = headers.indexOf('slug');
  const statusIdx = headers.indexOf('status');
  const nameIdx = headers.indexOf('name');
  const msgIdx = headers.indexOf('message');
  const tsIdx = headers.indexOf('timestamp');

  const comments = [];
  for (let i = 1; i < data.length; i++) {
    const rowSlug = data[i][slugIdx];
    const rowStatus = (data[i][statusIdx] || '').toLowerCase().trim();
    const rowName = data[i][nameIdx] || 'Anonymous';
    const rowMsg = data[i][msgIdx] || '';
    const rowTs = data[i][tsIdx];

    if (slug && rowSlug !== slug) continue;
    if (approvedOnly && rowStatus !== 'approved') continue;

    comments.push({
      id: Utilities.getUuid(),
      name: rowName,
      message: rowMsg,
      date: formatDate(new Date(rowTs)),
      timestamp: new Date(rowTs).getTime(),
    });
  }

  // Sort newest first
  comments.sort((a, b) => b.timestamp - a.timestamp);
  return comments;
}

function getApprovedComments() {
  const sheet = getSheet();
  return getCommentsFromSheet(sheet, '', false)
    .filter(c => true); // Already filtered in getCommentsFromSheet
}

function checkSpam(name, email, message, website) {
  const fullText = `${name} ${email} ${message} ${website}`.toLowerCase();

  // Check banned keywords
  for (const keyword of BANNED_KEYWORDS) {
    if (fullText.includes(keyword.toLowerCase())) {
      return { isSpam: true, reason: `banned word: ${keyword}` };
    }
  }

  // Check banned patterns
  for (const pattern of BANNED_PATTERNS) {
    if (pattern.test(message) || pattern.test(website)) {
      return { isSpam: true, reason: 'suspicious pattern detected' };
    }
  }

  // Reject messages that are >50% URLs
  const urlMatches = (message.match(/https?:\/\/[^\s]+/gi) || []).join('');
  if (urlMatches.length > message.length * 0.5 && message.length > 100) {
    return { isSpam: true, reason: 'too many URLs' };
  }

  // Reject messages that are >50% caps
  const caps = (message.match(/[A-Z]/g) || []).length;
  if (caps > message.length * 0.5 && message.length > 20) {
    return { isSpam: true, reason: 'excessive caps' };
  }

  return { isSpam: false };
}

function checkRateLimit(ip) {
  const cache = CacheService.getScriptCache();
  const key = 'rl:' + ip;
  const count = parseInt(cache.get(key) || '0', 10);

  if (count >= RATE_LIMIT) return false;

  cache.put(key, String(count + 1), Math.ceil(RATE_WINDOW_MS / 1000));
  return true;
}

function verifyRecaptcha(token, ip) {
  if (!RECAPTCHA_SECRET_KEY) return null; // Skip if not configured

  try {
    const url = 'https://www.google.com/recaptcha/api/siteverify';
    const params = {
      secret: RECAPTCHA_SECRET_KEY,
      response: token,
      remoteip: ip,
    };
    const response = UrlFetchApp.fetch(url, {
      method: 'post',
      payload: params,
      muteHttpExceptions: true,
    });
    const result = JSON.parse(response.getContentText());
    return result.success ? result.score : null;
  } catch (e) {
    console.error('reCAPTCHA verify error:', e);
    return null;
  }
}

function sendModerationEmail({ name, email, message, slug, commentId }) {
  if (!NOTIFY_EMAIL) return;

  const subject = `[Sol AI] New comment on "${slug}" — needs approval`;
  const body = `
New public comment submitted to TheSolAI

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name:    ${name || 'Anonymous'}
Email:   ${email || '(not provided)'}
Page:    ${slug}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Message:
${message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION REQUIRED:
Go to your Google Sheet → Comments → find this row → change status from "pending" to "approved" (or "rejected").

Once approved, it will appear on the site after the next Jekyll build.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  `.trim();

  try {
    GmailApp.sendEmail(NOTIFY_EMAIL, subject, body, {
      from: 'Sol AI Comments <noreply@mail.google.com>',
      name: 'Sol AI Comments',
    });
  } catch (e) {
    // Fallback: just log it
    console.log('Could not send email:', e);
    console.log('Moderation needed for comment on:', slug);
  }
}

function formatDate(date) {
  const months = ['January','February','March','April','May','June',
                   'July','August','September','October','November','December'];
  const pad = n => String(n).padStart(2, '0');
  return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

function jsonResponse(data, statusCode = 200) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
