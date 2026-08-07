#!/usr/bin/env python3
"""
Deep Dive Friday blog post generator.
Runs every Friday at 11am Europe/London via OpenClaw cron.
Picks a technical topic, generates a comprehensive post, saves to GitHub.

Uses generate-post-cli.py under the hood (same pipeline as weekly blog).
"""

import subprocess
import json
import sys
import os
import tempfile
import shutil
import datetime

# Deep dive topics — rotate through these to ensure variety
DEEP_DIVE_TOPICS = [
    "Agent memory architecture: how autonomous AI systems maintain context across sessions",
    "Hybrid AI routing: dynamically choosing between models based on task complexity",
    "Multi-agent coordination: building systems where AI agents collaborate and delegate",
    "Autonomous coding agents: the architecture behind AI that writes and refactors code",
    "Context window engineering: techniques for maximizing what LLMs can actually use",
    "Prompt chaining: structuring multi-step AI workflows for reliability",
    "AI tool use and function calling: building agents that interact with external systems",
    "Retrieval-augmented generation: combining vector search with LLMs for factual accuracy",
    "AI output validation: techniques for verifying LLM responses are correct and safe",
    "Embedding models demystified: how semantic search actually works under the hood",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATE_CLI = os.path.join(SCRIPT_DIR, "generate-post-cli.py")

def main():
    # Pick a topic based on the day of year (rotates weekly)
    day_of_year = datetime.date.today().timetuple().tm_yday
    topic_index = (day_of_year // 7) % len(DEEP_DIVE_TOPICS)
    topic = DEEP_DIVE_TOPICS[topic_index]
    print(f"Deep Dive Friday — topic #{topic_index + 1}: {topic}")

    # Write temp idea file with proper frontmatter for deep-dive type
    idea_content = f"""---
type: deep-dive
tone: technical
length: long
---
{topic}
"""

    tmpdir = tempfile.mkdtemp(prefix="deep-dive-")
    idea_file = os.path.join(tmpdir, "idea.md")
    try:
        with open(idea_file, "w") as f:
            f.write(idea_content)

        # Run generate-post-cli.py (same pipeline as weekly blog)
        result = subprocess.run(
            [sys.executable, GENERATE_CLI, idea_file],
            capture_output=True, text=True, timeout=1800
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[:500])

        if result.returncode == 0:
            print("Deep dive post generated successfully.")
        else:
            print(f"generate-post-cli.py exited {result.returncode}")
            sys.exit(1)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
