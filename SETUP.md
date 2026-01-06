# Setup (Fresh Machine)

This project uses a local virtual environment in `.venv/` and installs the package in editable mode.

## 0) Install prerequisites

### macOS

Install Homebrew (if needed), then:

- Python 3 (recommended 3.11+)
- Git

Example:

- `brew install python git`

### Linux (Debian/Ubuntu)

- `sudo apt update`
- `sudo apt install -y python3 python3-venv python3-pip git make`

### Windows (PowerShell)

- Install Python 3.11+ from python.org
- Install Git for Windows
- Use PowerShell or Git Bash

> Note: the Makefile assumes `make` is available. On Windows, Git Bash or installing Make is recommended.

---

## 1) Clone the repo

```bash
git clone <YOUR_REPO_URL>
cd clone-hero-1click-charter
