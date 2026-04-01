---
module: "09 — Git for Application Developers"
exercise: "Exercise 2 — Feature Branch Workflow and Pull Request"
duration: "30 minutes"
---

# Exercise 2 — Feature Branch Workflow and Pull Request

## Objective

Practice the complete feature branch lifecycle: **create → develop → push → PR → merge**

---

## Part A: Create and Work on Feature Branch (Dev A Role)

1. Switch to `main` and pull the latest changes:
   ```bash
   git checkout main
   git pull origin main
   ```
2. Create and switch to a new feature branch:
   ```bash
   git checkout -b feature/add-validator
   ```
3. Open `validator.py`
4. Modify the `validate_input` function — change the error message text:
   - From: `"Missing key"`
   - To: `"Required key missing"`
5. Save the file
6. Stage the change:
   ```bash
   git add validator.py
   ```
7. Commit the change:
   ```bash
   git commit -m "feat: improve error message in validate_input"
   ```
8. Push the branch to GitHub:
   ```bash
   git push origin feature/add-validator
   ```

---

## Part B: Create a Second Feature Branch (Dev B Role)

1. Switch back to `main`:
   ```bash
   git checkout main
   ```
2. Create and switch to a second feature branch:
   ```bash
   git checkout -b feature/update-schema
   ```
3. Open `validator.py`
4. Modify the `validate_schema` function — add a check for a new required key `"category"` (must be a non-empty string)
5. In the **same file**, also update the error message in the `validate_input` function — change it to:
   - `"Validation error: missing key"`

> **IMPORTANT**: This must be a **different** wording from what Part A used (`"Required key missing"`). Both branches now independently change the same line from the original `"Missing key"` to different new values. This divergence guarantees a real merge conflict in Exercise 3.

6. Save the file
7. Stage the change:
   ```bash
   git add validator.py
   ```
8. Commit the change:
   ```bash
   git commit -m "feat: add category validation and update error message"
   ```
9. Push the branch to GitHub:
   ```bash
   git push origin feature/update-schema
   ```

---

## Part C: Open a Pull Request (feature/add-validator → main)

1. Go to your GitHub repository
2. Click **Pull Requests → New Pull Request**
3. Verify the **base branch** is `main` and the **compare branch** is `feature/add-validator`

> **Habit check**: Always confirm the base branch before submitting. GitHub defaults to `main` — verify the dropdown shows the intended target, especially in repos with many branches.

4. Set the **Title**: `feat: improve error message in validate_input`
5. Add a brief description of what changed and why
6. Click **Create Pull Request**
7. Review the diff — confirm only the error message line in `validator.py` changed
8. Click **Merge Pull Request → Confirm Merge**

> `main` now has `"Required key missing"`. Meanwhile `feature/update-schema` was branched from the **original** `main` and independently holds `"Validation error: missing key"` on the same line. Both branches diverged from the same ancestor in different directions — this sets up the guaranteed conflict in Exercise 3.

> **Note**: PRs can target any branch, not just `main`. Branch-to-branch PRs are common in larger teams using integration branches (e.g., `develop`, `staging`). The mechanics are identical — only the base branch dropdown changes.
