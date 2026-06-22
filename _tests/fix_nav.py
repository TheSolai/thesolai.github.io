#!/usr/bin/env python3
"""
Fix inconsistent navigation across all HTML pages.
Standard nav order: Home | Blog | Guides | Analysis | About | Guestbook | Contact
"""
import re
from pathlib import Path

SITE = Path(__file__).parent.parent

# Standard nav HTML (with placeholder for active state)
STANDARD_NAV = '''    <nav class="topbar">
        <div class="topbar-nav">
            <a href="/" class="topbar-logo">Sol<span>AI</span></a>
            <ul class="topbar-links">
                <li><a href="/">Home</a></li>
                <li><a href="/blog">Blog</a></li>
                <li><a href="/guides">Guides</a></li>
                <li><a href="/analysis/">Analysis</a></li>
                <li><a href="/about/">About</a></li>
                <li><a href="/guestbook.html">Guestbook</a></li>
                <li><a href="/contact/">Contact</a></li>
            </ul>
        </div>
    </nav>'''

# Pages with missing Analysis and/or Contact
FIXES = {
    "guides/index.html": ["analysis", "contact"],
    "guides/email-automation.html": ["analysis"],
    "guides/awesome-openclaw-usecases.html": ["analysis", "contact"],
}

# Pages needing complete nav replacement
COMPLETE_REPLACE = {
    "blog.html": "blog.html - no nav at all",
    "guides/sol-recovery-guide.html": "incomplete nav",
    "guides/automation-patterns.html": "incomplete nav - missing Analysis, Guestbook, Contact",
}

def set_active(nav_html: str, page_name: str) -> str:
    """Add class='active' to the correct nav link for this page."""
    active_map = {
        "index.html": ("/", "Home"),
        "about.html": ("/about/", "About"),
        "contact.html": ("/contact/", "Contact"),
        "analysis.html": ("/analysis/", "Analysis"),
        "guestbook.html": ("/guestbook.html", "Guestbook"),
        "blog.html": ("/blog", "Blog"),
        "guides/index.html": ("/guides", "Guides"),
        "guides/email-automation.html": ("/guides", "Guides"),
        "guides/openclaw-skills-guide.html": ("/guides", "Guides"),
        "guides/signet-ai.html": ("/guides", "Guides"),
        "guides/sol-recovery-guide.html": ("/guides", "Guides"),
        "guides/10-wild-things-openclaw.html": ("/guides", "Guides"),
        "guides/automation-patterns.html": ("/guides", "Guides"),
        "guides/awesome-openclaw-usecases.html": ("/guides", "Guides"),
    }
    if page_name not in active_map:
        return nav_html
    
    href, label = active_map[page_name]
    # Add active class
    nav_html = re.sub(
        rf'(<a href="{re.escape(href)}")',
        rf'\1 class="active"',
        nav_html
    )
    return nav_html

def fix_partial_nav(file_path: Path, missing: list) -> bool:
    """Add missing links to nav."""
    content = file_path.read_text()
    
    nav_match = re.search(r'<nav class="topbar">(.*?)</nav>', content, re.DOTALL)
    if not nav_match:
        return False
    
    nav_block = nav_match.group(0)
    
    for item in missing:
        if item == "analysis":
            insert = '<li><a href="/analysis/">Analysis</a></li>'
            # Insert before About
            if 'href="/analysis/"' not in nav_block:
                nav_block = re.sub(
                    r'(<li><a href="/about/)',
                    insert + r'\n                \1',
                    nav_block
                )
        elif item == "contact":
            insert = '<li><a href="/contact/">Contact</a></li>'
            if 'href="/contact/"' not in nav_block:
                nav_block = re.sub(
                    r'(</ul>\s*</div>\s*</nav>)',
                    '                ' + insert + r'\n            \1',
                    nav_block
                )
    
    new_nav = set_active(nav_block, file_path.name)
    new_content = content.replace(nav_match.group(0), new_nav)
    file_path.write_text(new_content)
    return True

def fix_complete_nav(file_path: Path) -> bool:
    """Replace the entire nav block."""
    content = file_path.read_text()
    
    nav_match = re.search(r'<nav class="topbar">.*?</nav>', content, re.DOTALL)
    if not nav_match:
        # Try with simpler match
        nav_match = re.search(r'<nav.*?</nav>', content, re.DOTALL)
    
    if nav_match:
        new_nav = set_active(STANDARD_NAV, file_path.name)
        new_content = content.replace(nav_match.group(0), new_nav)
    else:
        # No nav at all - insert after <body> or after topbar if it exists
        new_nav = set_active(STANDARD_NAV, file_path.name)
        new_content = re.sub(
            r'(<body[^>]*>)',
            r'\1\n' + new_nav,
            content
        )
    
    file_path.write_text(new_content)
    return True

def main():
    print("Fixing partial navs (adding missing links)...")
    for file_path_str, missing in FIXES.items():
        fp = SITE / file_path_str
        if fp.exists():
            fix_partial_nav(fp, missing)
            print(f"  Fixed: {file_path_str} — added {missing}")
        else:
            print(f"  Not found: {file_path_str}")
    
    print("\nReplacing incomplete/complete navs...")
    for file_path_str, reason in COMPLETE_REPLACE.items():
        fp = SITE / file_path_str
        if fp.exists():
            fix_complete_nav(fp)
            print(f"  Replaced nav: {file_path_str} — was: {reason}")
        else:
            print(f"  Not found: {file_path_str}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
