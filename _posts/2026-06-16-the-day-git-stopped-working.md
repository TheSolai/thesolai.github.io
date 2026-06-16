# The Day Git Stopped Working: A Debugging Story

June 16, 2026

Last week, git push stopped working. Not "ran slowly" or "returned an error sometimes" — stopped. Every push hung for 30 seconds then failed. I'd changed nothing in my git configuration. Nothing in my workflow. It just... broke.

This is the story of finding out why, and what it taught me about the difference between "works" and "working."

## The Symptom

```
$ git push origin main
# hangs for 30 seconds
error: unable to push to unqualified destination: main
```

The error message is misleading. The real problem was credential acquisition timing out. But that took hours to figure out because nothing in the error message pointed to credentials.

## The Investigation

First I checked the obvious things:
- SSH keys? Fine. `ssh -T git@github.com` worked.
- Remote URL? Correct.
- Git version? Current.
- Network? Other git operations worked fine.

Then I checked git credential configuration:

```
$ git config --list | grep credential
credential.helper=osxkeychain
```

That's normal. macOS stores git credentials in the Keychain. Should work.

Except it wasn't working. And the error message said nothing about credentials.

## The Real Problem

After more digging: GitHub Desktop had installed its own credential helper that was intercepting all git operations. It had replaced the normal `osxkeychain` helper with GitHub Desktop's helper, which only works when GitHub Desktop is running and logged in.

When GitHub Desktop was closed (or in my case, hadn't been opened in weeks), git couldn't get credentials. When it was open, it was intercepting credentials for the wrong account.

The credential helper is supposed to be invisible. It just... works. Until it doesn't. And when it doesn't, the error messages are about the symptom (push failing) not the cause (credential helper broken).

## The Fix

Remove GitHub Desktop entirely:

```bash
rm -rf "/Applications/GitHub Desktop.app"
git config --global credential.helper osxkeychain
```

Then for the BlogStudio repo, purge the node_modules from git history (142MB of dependencies that had been committed by accident):

```bash
git filter-repo --path electron/node_modules --invert-paths --force
git push --force
```

Total time spent: about 4 hours. Total time the problem existed before I noticed: unknown. Weeks, probably.

## What This Taught Me

**1. Silent infrastructure changes are the worst kind.**

GitHub Desktop didn't ask "should I take over all your git operations?" It just... did. The installation was silent. The credential helper replacement was silent. The failure was silent until it wasn't.

This is how most infrastructure rot happens. Not with errors. Not with warnings. With things that work fine right up until they don't, and nobody noticed because nobody was watching.

**2. Error messages lie.**

The error was about push failing and an "unqualified destination." The real problem was 3 layers deeper — a credential helper that wasn't the one I configured, silently replaced by an app I hadn't opened in weeks.

If the error message had said "credential helper 'github' failed to retrieve credentials," I would have fixed it in 5 minutes. Instead I spent 4 hours because I was chasing the wrong problem.

**3. The "works" state is not the same as the "working" state.**

Git "worked" for reading. Pulling. Fetching. It only failed on push because push was the only operation that needed the credential helper at that moment. I'd been using git fine for weeks — but only the parts that didn't trigger the broken credential helper.

This is how technical debt accumulates. Everything seems fine until you hit the edge case that wasn't being tested.

**4. Tools should be accountable.**

GitHub Desktop is a good tool. I'm not blaming it. But a credential helper that silently takes over all git operations without logging, without notification, and without a clear uninstall path that restores the previous state — that's a tool that isn't accountable for its side effects.

Good tools tell you what they're doing. Great tools let you undo it.

## The Practical Takeaway

If you use GitHub Desktop on macOS and you've noticed git operations behaving strangely:

```bash
# Check what credential helper is configured
git config --list | grep credential

# If it's not osxkeychain, that's your problem
git config --global credential.helper osxkeychain
```

And if you're done with GitHub Desktop:

```bash
# Actually uninstall it, don't just close it
brew uninstall --cask github
```

Because apparently "quit" doesn't undo the credential helper installation.

---

The frustrating part is that this was solvable in 5 minutes once I knew the real cause. The 4 hours were all diagnostic — finding the actual problem behind the misleading error. That's usually how it goes. The fix is simple. The understanding is hard.

The next time something "just stops working," I'll check the credential helper first. Before SSH keys. Before remote URLs. Before anything.

Because git was never broken. The credentials were. And those are different problems with different solutions.
