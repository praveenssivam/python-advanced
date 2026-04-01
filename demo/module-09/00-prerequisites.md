---
module: "09 — Git for Application Developers"
exercise: "Prerequisites — Before the Session Starts"
duration: "15 minutes"
---

# Prerequisites — Before the Session Starts

## Tools Required

1. **Git 2.30+** — verify with:
   ```bash
   git --version
   ```
2. **Python 3.11+** — verify with:
   ```bash
   python3 --version   # Linux / macOS
   python --version    # Windows
   ```
3. **VS Code** — with the **GitLens** extension recommended
4. **A GitHub account** — free tier is sufficient (github.com)

---

## Git Identity Setup

1. Set your global name:
   ```bash
   git config --global user.name "Your Name"
   ```
2. Set your global email:
   ```bash
   git config --global user.email "you@example.com"
   ```
3. Verify the settings were saved:
   ```bash
   git config --list
   ```

> Every commit you make is attributed to this identity. If this is not set, Git will use a system default that may not reflect your name correctly in GitHub.

---

## Generate a Classic PAT on GitHub

1. Click your **profile photo** (top-right) → **Settings**
2. In the left sidebar, scroll to the bottom → click **Developer settings**
3. Navigate to **Personal access tokens → Tokens (classic)**
4. Click **Generate new token → Generate new token (classic)**
5. In the **Note** field, enter a descriptive name: `python-advanced-lab`
6. Set **Expiration** to **90 days** — this covers the full course duration
7. Under **Select scopes**, check **`repo`** (full control of private repositories)
8. Click **Generate token** at the bottom

> **WARNING**: Copy and save the token immediately. GitHub shows it **only once**. Store it in a password manager or a secure note. If you lose it, you must generate a new one.

> **Do NOT use Fine-grained PAT** — it has additional restrictions that will cause issues during this lab. Always select **Tokens (classic)**.

---

## Configure Git Credential Helper

This stores your PAT so you are not prompted on every push.

### Windows

```bash
git config --global credential.helper manager
```

> Windows Git Credential Manager is usually pre-configured. Run the command above to verify it is set.

### macOS

```bash
git config --global credential.helper osxkeychain
```

### Linux

```bash
git config --global credential.helper store
```

> On Linux, `store` saves credentials in plaintext at `~/.git-credentials`. This is acceptable for a training environment; use `cache` or a secrets service for production machines.

---

## Verify Your Existing Project

1. Navigate to your validation-service project folder:
   ```bash
   cd validation-service
   ```
2. Run the test suite to confirm everything passes before the lab starts:
   ```bash
   pytest tests/
   ```
3. Confirm the project structure includes all required files:
   - `main.py`
   - `validator.py`
   - `tests/`
   - `requirements.txt`

> All tests must be green before proceeding to Exercise 1. Fix any failures before the session begins.
