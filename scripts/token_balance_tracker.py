#!/usr/bin/env python3
"""
MiniMax Token/Credits Tracker
Fetches remaining token plan quota from MiniMax API.
Run: python3 token_balance_tracker.py

Saves output to ~/.openclaw/workspace/memory/minimax-balance.json
"""
import os
import json
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("MINIMAX_API_KEY", "sk-cp-FnVbYYLCuhNWNSPjJf8pI8bEJxIyTOWEGcbwa6X8ims68uJ1An8egdHr16K9XsAIs7Apx8FVdpbQcqJp-VxbALD9MUd6SiIFJsLrSmGNhBx5w7Dqf70Ev5o")
TOKEN_PLAN_URL = "https://api.minimax.io/v1/token_plan/remains"
STATE_FILE = os.path.expanduser("~/.openclaw/workspace/memory/minimax-balance.json")

def fetch_token_plan():
    """Fetch token plan remaining quota."""
    try:
        resp = requests.get(
            TOKEN_PLAN_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()
        return {"error": f"HTTP {resp.status_code}", "body": resp.text[:200]}
    except Exception as e:
        return {"error": str(e)}

def parse_remains_time(ms):
    """Convert milliseconds to human readable."""
    if not ms or ms <= 0:
        return "exhausted"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.0f}m"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"

def format_output(data):
    """Format the output nicely."""
    output = []
    output.append(f"MiniMax Token Plan Status — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 55)

    if "error" in data:
        output.append(f"Error: {data['error']}")
        return "\n".join(output)

    model_remains = data.get("model_remains", [])

    for plan in model_remains:
        model = plan.get("model_name", "unknown")
        interval_pct = plan.get("current_interval_remaining_percent", 0)
        weekly_pct = plan.get("current_weekly_remaining_percent", 0)
        interval_remaining = parse_remains_time(plan.get("remains_time"))
        weekly_remaining = parse_remains_time(plan.get("weekly_remains_time"))

        # Interval reset time
        interval_end = plan.get("end_time")
        if interval_end:
            dt = datetime.fromtimestamp(interval_end / 1000)
            interval_reset = dt.strftime("%H:%M %Z")
        else:
            interval_reset = "unknown"

        weekly_end = plan.get("weekly_end_time")
        if weekly_end:
            dt = datetime.fromtimestamp(weekly_end / 1000)
            weekly_reset = dt.strftime("%a %b %d %H:%M %Z")
        else:
            weekly_reset = "unknown"

        icon = "📦" if model == "general" else "🎬"
        output.append(f"\n{icon} {model.upper()}")
        output.append(f"   Rolling 5h window: {interval_pct}% remaining ({interval_remaining} left)")
        output.append(f"   Resets: ~{interval_reset}")
        output.append(f"   Weekly window:    {weekly_pct}% remaining ({weekly_remaining} left)")
        output.append(f"   Resets: {weekly_reset}")

        # Alert if low
        if interval_pct < 20:
            output.append("   ⚠️  LOW — less than 20% remaining in rolling window!")
        elif interval_pct < 50:
            output.append("   🟡 Getting low — consider credits top-up")

    output.append("")
    return "\n".join(output)

def main():
    data = fetch_token_plan()
    output = format_output(data)
    print(output)

    # Save to state file
    state = {
        "last_check": {
            "timestamp": datetime.now().isoformat(),
            "raw": data
        }
    }
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

if __name__ == "__main__":
    main()
