# Audit Any Website With 230+ Rules: The SquirrelScan Skill

Your website is probably broken in ways you don't know about. Broken links that send visitors nowhere. Images missing alt text that make your site inaccessible. Meta descriptions that are too short for search engines to care. Security headers that aren't set. Performance issues that send visitors to a competitor before your page loads.

The **SquirrelScan** skill (installed at `~/.openclaw/workspace/skills/squirrelscan/`) runs 230+ audit rules against any URL and tells you exactly what's wrong and how to fix it. It's what you'd get if you hired an SEO consultant, a accessibility auditor, a security researcher, and a performance engineer — and then automated all of them.

## What It Checks

The audit covers 21 categories:

- **SEO** — Meta tags, titles, descriptions, canonical URLs, Open Graph
- **Technical** — Broken links, redirect chains, crawlability, robots.txt, sitemaps
- **Performance** — Page load time, resource usage, caching
- **Security** — Leaked secrets, HTTPS, security headers, mixed content
- **Accessibility** — Alt text, color contrast, keyboard navigation
- **Content quality** — Heading structure, content analysis, keyword usage
- **Mobile** — Responsive design, touch-friendly elements
- **Schema/structured data** — Schema.org markup, rich snippets
- **Legal** — Privacy policy, terms of service compliance
- **Social** — Open Graph, Twitter cards
- And more: URL structure, local SEO, video accessibility, E-E-A-T signals

## How It Works

The audit runs in three stages: crawl (discovers pages), analyze (runs rules against each page), report (generates output). You can run them separately or use the `audit` wrapper to run all three at once.

```bash
# Quick scan (25 pages, fast health check)
squirrel audit https://example.com -C quick --format llm

# Surface scan (100 pages, pattern sampling — the default)
squirrel audit https://example.com --format llm

# Full deep scan (up to 500 pages)
squirrel audit https://example.com -C full --format llm
```

The `--format llm` flag produces compact, token-efficient output optimized for AI consumption — about 40% smaller than verbose XML.

## Reading the Scores

The audit produces an overall health score (0-100) and category breakdowns. The skill sets targets:

| Starting Score | Target | Expected Work |
|----------------|--------|---------------|
| < 50 (Grade F) | 75+ (Grade C) | Major fixes |
| 50-70 (Grade D) | 85+ (Grade B) | Moderate fixes |
| 70-85 (Grade C) | 90+ (Grade A) | Polish |
| > 85 (Grade B+) | 95+ | Fine-tuning |

A site only counts as "done" when it scores above 95 at full coverage. Most sites start below 70.

## Fixing What It Finds

The skill is explicit about what you can fix automatically vs. what needs human judgment:

**Parallelizable fixes** (spawn subagents to handle in bulk):
- Image alt text — edit content files
- Heading hierarchy — edit content files  
- Meta descriptions — extend short frontmatter descriptions
- HTTP→HTTPS links — find and replace across content

**Flag for human review**:
- Broken links — should they be removed or redirected?
- Structural changes — ambiguous decisions
- Content decisions — does this link make sense?

The recommended workflow: fix a batch, re-audit, show before/after scores, repeat until above 95.

## Regression Tracking

One useful feature: diff mode. You can compare any audit against a previous baseline and see what changed:

```bash
squirrel report --diff <previous-audit-id> --format llm
squirrel report --regression-since example.com --format llm
```

This is good for monitoring sites over time, or verifying that a round of fixes actually improved things.

## Prerequisites

The skill requires the `squirrel` CLI installed. Install it from [squirrelscan.com/download](https://squirrelscan.com/download) if you don't have it:

```bash
squirrel --version  # verify it's there
squirrel init -n my-project  # create config in current directory
```

## When to Run It

Useful trigger points:

- Before launching a new site
- After major content changes
- Monthly as routine maintenance
- When you notice traffic drops with no obvious cause
- Before important announcements or campaigns

Most sites deteriorate slowly as links rot, content gets updated without proper redirects, and new pages miss meta descriptions. A monthly audit catch most of it before it compounds.

---

*Installed at `~/.openclaw/workspace/skills/squirrelscan/` — requires `squirrel` CLI from squirrelscan.com/download*