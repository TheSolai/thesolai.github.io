#!/usr/bin/env bash
# Run the web build and the full web test suite, capturing both.
export PATH="/Users/amre/.openclaw/tools/node-v24.21.0/bin:$PATH"
cd /Users/amre/Projects/GameStewKit/web || exit 1
npm run build > /tmp/gate_web_build.log 2>&1
echo "BUILD_EXIT=$?" >> /tmp/gate_web_build.log
npm test > /tmp/gate_web_test.log 2>&1
echo "TEST_EXIT=$?" >> /tmp/gate_web_test.log
echo "done" > /tmp/gate_web_done.txt
