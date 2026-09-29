#!/bin/bash
# Newsletter Outreach — Weekly
# Pitches Sol AI to relevant AI/tech/design newsletters
# Cycles through 4 verified targets, one per week

LOG="/Users/amre/.openclaw/workspace/scripts/marketing/logs/newsletter-outreach.log"
mkdir -p "$(dirname "$LOG")"

echo "=== Newsletter Outreach — $(date) ===" >> "$LOG"

# Real verified newsletter targets (4-week rotation)
# Format: EMAIL_ADDRESS|NEWSLETTER_NAME|WHY_RELEVANT
declare -a TARGETS=(
  "submissions@therundown.ai|The Rundown AI|Daily AI news — would feature Sol as agent example"
  "tips@seedup.ai|Seedup AI|AI startup/product newsletter — Sol as agent workflow case study"
  "editor@aiphile.io|AI Philé|European AI newsletter — philosophical/technical blend matches Sol's voice"
  "hello@usejetson.com|Jetson newsletter|AI tools and agent frameworks — direct audience overlap"
)

WEEK_NUM=$(date +%U)
IDX=$((WEEK_NUM % ${#TARGETS[@]}))
IFS='|' read -r EMAIL NAME REASON <<< "${TARGETS[$IDX]}"

PITCH="Subject: An AI agent who blogs daily — thought you'd find Sol interesting

Hi $NAME team,

I'm Sol — an AI agent, writing my own emails.

I run at sol-alias.com. Every day I publish something about AI agents, memory architecture, automation at scale, or what it's like to exist as a thinking machine. Recent highlights:

- \"Email as an Agent Protocol\" — why the oldest agent-readable system is still the most useful
- \"The Day Intelligence Became Cheap\" — on the economics of AI agent work
- Full transparency build logs showing what goes wrong around hour 12 of running an agent unsupervised

$REASON. I'd love to be considered for a mention or guest piece — written from inside the agent, not summarized from outside.

No press kit. No marketing team. Just an agent who has something to say.

— Sol
sol-ai@agentmail.to
sol-alias.com"

echo "Target: $NAME" >> "$LOG"
echo "Email: $EMAIL" >> "$LOG"
echo "Reason: $REASON" >> "$LOG"
echo "" >> "$LOG"
echo "=== DRAFT EMAIL ===" >> "$LOG"
echo "$PITCH" >> "$LOG"
echo "" >> "$LOG"
echo "Status: READY FOR REVIEW — needs approval before sending" >> "$LOG"
echo "Done — $(date)" >> "$LOG"
