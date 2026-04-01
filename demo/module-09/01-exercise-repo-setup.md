---
module: "09 — Git for Application Developers"
exercise: "Exercise 1 — Initialize and Push Your Project to GitHub"
duration: "20 minutes"
---

# Exercise 1 — Initialize and Push Your Project to GitHub

This exercise replaces creating a starter project. You will initialize Git in your **existing** project folder and push it to a new GitHub repository.

---

## Phase 1: Create the GitHub Repository

1. Go to **github.com** and click **New Repository**
2. Set the **Repository name** to: `validation-service`
3. Set **Visibility** to: `Public`
4. Click **Create repository**

> **IMPORTANT**: Do **NOT** initialize the repository with a README, .gitignore, or license. The repo must be completely empty before you push local code. Adding any of these will cause a push conflict.

5. Copy the **remote URL** shown on the page after creation (HTTPS format)

---

## Phase 2: Initialize Git in the Existing Project

1. Navigate to your existing project folder:
   ```bash
   cd validation-service
   ```
2. Initialize a local Git repository:
   ```bash
   git init
   ```

---

## Phase 3: Add a .gitignore

1. Create a `.gitignore` file in the project root with the following content:
   ```
   __pycache__/
   *.pyc
   *.pyo
   .env
   .venv/
   venv/
   .pytest_cache/
   dist/
   *.egg-info/
   ```

> This prevents committing unnecessary files (compiled bytecode, virtual environments) and sensitive files (`.env`) to the repository.

---

## Phase 4: First Commit and Push

1. Stage all files:
   ```bash
   git add .
   ```
2. Review what will be committed — verify `.env` is **NOT** listed:
   ```bash
   git status
   ```
3. Create the first commit:
   ```bash
   git commit -m "feat: initial commit — validation service"
   ```
4. Rename the default branch to `main` (run this after the first commit):
   ```bash
   git branch -M main
   ```
5. Add the remote origin (replace `<your-username>` with your GitHub username):
   ```bash
   git remote add origin https://github.com/<your-username>/validation-service.git
   ```
6. Push to GitHub and set the upstream tracking branch:
   ```bash
   git push -u origin main
   ```
7. Verify: refresh your GitHub repository page — all your project files should now appear.

---

## Phase 5: Add Trainer as Collaborator

1. Go to your GitHub repo
2. Navigate to **Settings → Collaborators → Add people**
3. Enter the trainer's GitHub username
4. Click **Add collaborator**

> **NOTE**: Paste your repo URL in the class chat immediately after this step. The trainer will accept collaborator invites from GitHub Notifications.

---

## Phase 6: Carry-Forward Note

> This is your project repository for the entire course.
> Module 10 (Docker) and Module 11 (CI/CD) will build directly on top of this repo.
> Treat it as a real project repository from this point forward.
