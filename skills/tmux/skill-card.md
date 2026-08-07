## Description: <br>
Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[steipete](https://clawhub.ai/user/steipete) <br>

### License/Terms of Use: <br>


## Use Case: <br>
Developers and engineers use this skill when an agent needs an interactive TTY to manage tmux sessions, send input to panes, capture pane output, wait for prompts, and clean up sessions. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: An agent controlling tmux can send keystrokes to panes and capture pane output, including unintended or sensitive sessions. <br>
Mitigation: Use a private socket, verify session and pane targets before sending input, and avoid targeting panes that may contain secrets. <br>
Risk: Session cleanup commands such as kill-session or kill-server can terminate active work if aimed at the wrong session or socket. <br>
Mitigation: Verify session names and socket paths before running cleanup commands. <br>
Risk: Autonomous agent examples can modify repositories through long-running interactive sessions. <br>
Mitigation: Review repository changes made by autonomous agents before relying on or deploying them. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/steipete/skills/tmux) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with Bash command examples] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Requires tmux on PATH and is gated to macOS and Linux; Windows users are directed to run tmux inside WSL.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
