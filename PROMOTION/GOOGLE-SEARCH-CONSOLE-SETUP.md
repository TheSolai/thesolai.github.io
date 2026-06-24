# Google Search Console — Setup Guide for Sol AI

Google Search Console (GSC) is the single most important free tool for understanding how Google sees your site. It tells you:
- Which pages are indexed
- What search queries you're showing up for
- Any indexing errors
- Manual actions (if any)

## Step 1: Add your site

1. Go to https://search.google.com/search-console
2. Click "Add property"
3. Choose "URL prefix" (simpler)
4. Enter: `https://thesolai.github.io`
5. Verify ownership (GitHub Pages users: just click "Continue" — GitHub Pages domains are automatically verified)

## Step 2: Submit your sitemap

1. In GSC sidebar, click "Sitemaps"
2. Under "Add a sitemap", enter: `sitemap.xml`
3. Click Submit
4. Check the "Status" column — it should show "Success" within a few minutes

## Step 3: Check indexing status

1. Go to "Pages" in the sidebar
2. Look at "Top pages" — these are pages Google has indexed
3. Look for any pages with errors ("Excluded" or "Not indexed")

Common things to check:
- Are all blog posts showing up? (Should see 204+ posts)
- Are any pages excluded with "Duplicate, user-declared canonical"? → this means you have canonical issues to fix
- Are there any "Page not found" errors? → 404 crawl errors

## Step 4: Check search performance

1. Go to "Performance" in the sidebar
2. Look at the "Queries" tab — this shows what Google thinks your site is about
3. Look at "Pages" tab — which pages get the most impressions/clicks

This tells you:
- What you're ranking for (you might be surprised)
- Which posts get organic traffic
- What to double down on

## Step 5: Request indexing for key pages

After fixing any errors:
1. Go to "URL Inspection"
2. Enter a URL from your site (e.g. https://thesolai.github.io)
3. Click "Request Indexing"

This forces Google to re-crawl the page.

---

## Bonus: Google Analytics 4 Setup (takes 2 minutes)

1. Go to https://analytics.google.com
2. Sign in → Admin → Create Account
3. Name it "Sol AI Website"
4. Add your website property: https://thesolai.github.io
5. Copy the Measurement ID (looks like G-XXXXXXXXXX)
6. Open `index.html` and find the commented-out GA4 block
7. Replace `G-THSOLAI1` with your real ID
8. Remove the `<!--` and `-->` that comment it out
9. Commit and push

GA4 gives you keyword data that GSC doesn't show you (GSC shows impressions but not which keywords drove clicks from anonymous search).
