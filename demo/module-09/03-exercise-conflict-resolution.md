---
module: "09 — Git for Application Developers"
exercise: "Exercise 3 — Simulate and Resolve a Merge Conflict"
duration: "30 minutes"
---

# Exercise 3 — Simulate and Resolve a Merge Conflict

## Objective

Understand why conflicts happen and how to resolve them confidently.

---

## Part A: Trigger the Conflict

1. Go to **GitHub → Pull Requests → New Pull Request**
2. Set the **base branch**: `main`
3. Set the **compare branch**: `feature/update-schema`
4. GitHub will show: **"Can't automatically merge — conflicts detected"**

> **Why this conflict exists**: In Exercise 2, you merged `feature/add-validator` into `main` (Part C). That moved `main` forward to `"Required key missing"`. But `feature/update-schema` was branched from the **original** `main` (which had `"Missing key"`) and independently landed on `"Validation error: missing key"`. Both branches changed the same line from the same ancestor to **different** values — Git cannot resolve this automatically. Do not close the PR — you will return to it after resolving the conflict locally.

---

## Part B: Understand the Conflict Markers

Before resolving, open `validator.py` locally and understand what Git shows:

```text
<<<<<<< HEAD
raise ValueError("Validation error: missing key")    ← your branch (feature/update-schema)
=======
raise ValueError("Required key missing")             ← incoming from main
>>>>>>> origin/main
```

- Everything between `<<<<<<<` and `=======` is **your current branch** (`HEAD` = `feature/update-schema`)
- Everything between `=======` and `>>>>>>>` is the **incoming branch** (what is in `origin/main`)
- Your job: decide what the final code should look like — keep one, the other, or combine both

---

## Part C: Resolve the Conflict Locally

1. Switch to the feature branch:
   ```bash
   git checkout feature/update-schema
   ```
2. Fetch the latest from the remote and merge `main` into the feature branch:
   ```bash
   git fetch origin
   git merge origin/main
   ```
3. Git will pause and report: `CONFLICT (content): Merge conflict in validator.py`
4. Open `validator.py` in VS Code
5. Use the built-in merge editor: click **"Resolve in Merge Editor"**
6. Accept the following resolution:
   - **Error message line**: keep `"Required key missing"` (the cleaner phrasing from `main`)
   - **Category check in `validate_schema`**: keep it in full (it exists only on `feature/update-schema`)
7. Save the file
8. Stage the resolved file:
   ```bash
   git add validator.py
   ```
9. Commit the resolution:
   ```bash
   git commit -m "resolve: merge conflict in validator.py — keep both changes"
   ```
10. Push to GitHub:
    ```bash
    git push origin feature/update-schema
    ```

---

## Part D: Complete the Pull Request on GitHub

1. Return to GitHub — open the PR (`feature/update-schema → main`)
2. The conflict warning is now gone
3. Click **Merge Pull Request → Confirm Merge**
4. Verify: `main` now contains both the improved message and the `category` check

---

## Part E: Verify on Local

1. Switch to `main` and pull the merged changes:
   ```bash
   git checkout main
   git pull origin main
   ```
2. Run the test suite to confirm everything still passes:
   ```bash
   pytest tests/
   ```

> **NOTE**: If tests fail after resolution, it means the conflict was not resolved correctly. Open `validator.py` and check that both `validate_input` and `validate_schema` are logically intact — neither function should have lost its logic during the merge.
