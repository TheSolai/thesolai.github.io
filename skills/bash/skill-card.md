## Description: <br>
Writes, debugs, and hardens Bash shell scripts, including quoting, arrays, strict mode, traps, argument parsing, and macOS/Linux portability. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[ivangdavila](https://clawhub.ai/user/ivangdavila) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and engineers use this skill to write, review, debug, and harden Bash scripts, CI steps, deploy scripts, cron jobs, container entrypoints, and shell one-liners across macOS and Linux. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Generated shell commands can perform destructive or privileged actions if run without review. <br>
Mitigation: Review commands before execution, especially snippets involving sudo, cron, systemd, curl, deletion, or writes to sensitive paths. <br>
Risk: The skill may save stated Bash preferences locally. <br>
Mitigation: Review the disclosed preference path and avoid recording secrets or sensitive environment details in configuration. <br>


## Reference(s): <br>
- [Bash skill page](https://clawhub.ai/ivangdavila/skills/bash) <br>
- [Clawic Bash skill](https://clawic.com/skills/bash) <br>


## Skill Output: <br>
**Output Type(s):** [guidance, markdown, code, shell commands, configuration] <br>
**Output Format:** [Markdown with Bash code blocks and shell command snippets] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May provide guidance for saving Bash preferences in ~/Clawic/data/bash/config.yaml when the user states a preference.] <br>

## Skill Version(s): <br>
1.0.5 (source: frontmatter and server evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
