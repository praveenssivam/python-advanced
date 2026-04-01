---
module: "09 — Git for Application Developers"
exercise: "Quick Reference Card — Git Module 9"
duration: "Reference"
---

# Quick Reference Card — Git Module 9

## Git Identity

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --list
```

---

## PAT-Based Remote URL

```bash
# Use this format if Git prompts for credentials manually
https://<YOUR-PAT>@github.com/<username>/validation-service.git
```

---

## Branch Commands

```bash
git checkout -b feature/your-feature     # create and switch
git push origin feature/your-feature     # push branch to GitHub
git branch -a                            # list all branches
```

---

## PR Base Branch Reminder

Always check the **base branch dropdown** before creating a PR.  
GitHub defaults to `main` — change it deliberately when targeting another branch.

---

## Conflict Markers

```text
<<<<<<< HEAD ← your current branch
your version of code
=======
their version of code
>>>>>>> incoming ← branch being merged in
```

---

## Conflict Resolution — 5 Steps

```bash
git fetch origin && git merge origin/main    # 1. pull in the conflicting branch
# 2. open the file — find and resolve conflict markers
git add validator.py                         # 3. stage the resolved file
git commit -m "resolve: conflict in ..."     # 4. commit the resolution
git push origin feature/your-branch         # 5. push — PR conflict is now cleared
```

---

## Tagging

```bash
git tag -a v1.0.0 -m "Release message"
git push origin v1.0.0
git show v1.0.0
```

---

## Common Errors

| Error | Likely Cause | Fix |
|---|---|---|
| Authentication failed | Wrong PAT or expired | Generate new Classic PAT, re-enter credentials |
| Fine-grained PAT errors | Wrong PAT type selected | Switch to Classic PAT with `repo` scope |
| PR conflict warning | Same lines edited in both branches | Follow Exercise 3 resolution steps |
| Tests fail after merge | Conflict resolution was incomplete | Re-open `validator.py`, check both functions |
