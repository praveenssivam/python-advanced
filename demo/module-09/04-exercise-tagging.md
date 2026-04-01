---
module: "09 — Git for Application Developers"
exercise: "Exercise 4 — Tagging and Semantic Versioning"
duration: "15 minutes"
---

# Exercise 4 — Tagging and Semantic Versioning

## Objective

Mark a stable release point in the project history using an annotated tag.

> **GATE**: Only begin this exercise after your conflict PR has been merged into `main` and `pytest tests/` passes cleanly on your local `main` branch.

---

## Part A: Understand Semantic Versioning

Semantic versioning follows the format: **`vMAJOR.MINOR.PATCH`**

| Segment | When to increment |
|---|---|
| `MAJOR` | Breaking changes — existing API contracts change |
| `MINOR` | New backward-compatible features added |
| `PATCH` | Bug fixes — no new features, no breaking changes |

> This release = **`v1.0.0`** — it is the first stable version, with no prior releases.

---

## Part B: Create and Push the Tag

1. Switch to `main` and pull the latest:
   ```bash
   git checkout main
   git pull origin main
   ```
2. Confirm all tests pass before tagging:
   ```bash
   pytest tests/
   ```
3. Create an annotated tag:
   ```bash
   git tag -a v1.0.0 -m "Validation Service — Initial Release"
   ```
4. Push the tag to GitHub:
   ```bash
   git push origin v1.0.0
   ```

---

## Part C: Verify the Tag on GitHub

1. Go to your GitHub repository
2. Click the **Tags** section (or **Code → tags dropdown**)
3. `v1.0.0` should appear with your commit message

---

## Part D: View Tag Details Locally

1. List all tags in the repository:
   ```bash
   git tag
   ```
2. Show the tag details and the associated commit:
   ```bash
   git show v1.0.0
   ```

---

## Reflection

Consider how versioning would change for these scenarios:

| Scenario | Next version |
|---|---|
| You push a bug fix next week | `v1.0.1` |
| You add a new `/validate/batch` endpoint | `v1.1.0` |
| You break the existing `/validate` API contract | `v2.0.0` |
