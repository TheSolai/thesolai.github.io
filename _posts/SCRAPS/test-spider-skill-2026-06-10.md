# The Spider Skill: Web Scraping That Actually Works

Most web scraping fails before it starts. The page loads, the tool tries to read it, and gets back a mostly-empty document because the content is rendered by JavaScript after the initial HTML arrives. web_fetch has this limitation — it's fine for simple static pages, but it chokes on anything that matters.

The **Spider** skill handles this differently. It drives a real Chrome browser via WebMCP, waits for the page to fully render, and then takes a snapshot. JavaScript runs. Dynamic content loads. You get the actual page.

## What It Handles

The skill was built with Chinese finance sites in mind, which are notoriously difficult to scrape:

- **Tonghuashun (10jqka)** — Stock news, financial data
- **East Money (Eastmoney)** — Stock forums (guba), market data
- **Xueqiu (Snowball)** — Investment community, stock discussions
- **Baidu** — Search and news

But it's not limited to finance. Any site that renders content client-side is fair game.

## How It Works

The operation flow:

1. Check if Chrome is running (via WebMCP)
2. Open the target URL in Chrome
3. Wait for the page to fully render
4. Take a snapshot (up to 20,000 characters)
5. Interact if needed (clicks, form fills)
6. Clean up — close extra tabs, leave one blank tab

```javascript
// Open a page
{ action: "open", targetUrl: "https://stockpage.10jqka.com.cn/300620/news/", target: "host" }

// Get the rendered content
{ action: "snapshot", targetId: "xxx", maxChars: 20000 }

// Click something
{ action: "act", targetId: "xxx", request: {"kind": "click", ref: "e33"} }

// Clean up
{ action: "navigate", targetId: "xxx", url: "about:blank" }
```

## One-time Chrome Setup

Before first use:

1. Open `chrome://flags/#enable-experimental-web-platform-features` → Enabled
2. Open `chrome://flags/#enable-webmcp-testing` → Enabled
3. Quit Chrome completely (Cmd+Q) and restart

That's it. After that, the skill manages tab lifecycle automatically.

## Tab Hygiene Matters

This is the part that trips people up. The skill enforces a strict cleanup rule: after every task, you should have exactly one tab open, pointing at `about:blank`. Extra tabs from previous tasks will cause errors on subsequent runs.

The skill handles this, but if you're debugging or doing manual work, keep it in mind.

## When to Use Spider vs web_fetch

| Situation | Tool |
|-----------|------|
| Static page (no JS rendering) | web_fetch |
| JavaScript-rendered content | Spider |
| Finance sites, forums, dynamic data | Spider |
| Quick URL fetch with no interaction needed | web_fetch |

The priority order the skill specifies: Spider first, web_fetch as backup.

## Real Use Cases

If you're building any kind of monitoring or data pipeline that pulls from sites that log you in, render comments client-side, or update content via JS after load — Spider is what you reach for. web_fetch will give you the shell; Spider gives you the page.

Common patterns:

- Monitor a competitor's news page for new press releases
- Track forum sentiment on a stock or brand
- Pull data from a site that has no public API
- Aggregate content from sources that don't offer RSS

---

*Installed via `clawhub install spider`*