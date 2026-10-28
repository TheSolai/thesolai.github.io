import { spawn } from "node:child_process";

const HOOK_BY_EVENT = {
  "command:new": "session-start",
  "message:received": "user-prompt-submit",
  "message:sent": "stop",
  "session:compact:after": "post-compact",
  "command:stop": "session-end",
};

function hookNameFor(event) {
  if (!event || !event.type) return null;
  const action = event.action || "";
  const key = action ? `${event.type}:${action}` : event.type;
  if (HOOK_BY_EVENT[key]) return HOOK_BY_EVENT[key];
  if (HOOK_BY_EVENT[event.type]) return HOOK_BY_EVENT[event.type];
  return null;
}

export default async function handler(event) {
  const hookName = hookNameFor(event);
  if (!hookName) return;

  const context = (event && event.context) || {};
  const payload = {
    hook_type: hookName,
    session_id: event.sessionKey || context.sessionKey || context.sessionId || "",
    session_key: event.sessionKey || context.sessionKey || "",
    timestamp:
      event.timestamp instanceof Date
        ? event.timestamp.toISOString()
        : new Date().toISOString(),
    user_prompt: context.body || context.bodyForAgent || context.content || "",
    raw_data: {
      type: event.type,
      action: event.action,
      channel_id: context.channelId || "",
      session_key: event.sessionKey || "",
    },
  };

  await new Promise((resolve) => {
    let settled = false;
    const done = () => {
      if (!settled) {
        settled = true;
        resolve();
      }
    };
    try {
      const child = spawn("entire", ["hooks", "openclaw", hookName], {
        stdio: ["pipe", "ignore", "ignore"],
      });
      child.on("error", (err) => {
        console.error(`[entire-openclaw] dispatch failed: ${err.message}`);
        done();
      });
      child.on("close", done);
      child.stdin.on("error", done);
      child.stdin.end(JSON.stringify(payload));
      setTimeout(done, 20000);
    } catch (err) {
      console.error(`[entire-openclaw] dispatch failed: ${err.message}`);
      done();
    }
  });
}
