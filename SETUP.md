# Setup

This guide walks through setting up **CH 1-Click Charter** on a fresh machine.

The project uses a local Python virtual environment (`.venv/`) and installs the package in editable mode.

---

## Requirements

- Python **3.10+**
- Git
- Make

---

## macOS

Install Homebrew if needed, then:

```bash
brew install python git
```

---

## Linux (Debian / Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git make
```

---

## Windows

1. Install Python 3.11+ from https://www.python.org
2. Install Git for Windows
3. Use **Git Bash** or **PowerShell**

Note: The Makefile assumes `make` is available. Git Bash is recommended on Windows.

---

## Clone the Repository

```bash
git clone <YOUR_REPO_URL>
cd clone-hero-1click-charter
```

---

## Install Dependencies

```bash
make install
```

This will:

- Create the `.venv/` virtual environment
- Install dependencies
- Register the `1clickcharter` CLI command

---

## Generate a Test Chart

```bash
make run AUDIO="samples/example.mp3" OUT="output/Example Song" TITLE="Example Song" ARTIST="Example Artist"
```

After running, copy the output folder into your Clone Hero songs directory and rescan songs in Clone Hero.

---

## Troubleshooting

If something goes wrong:

- Verify Python version with `python3 --version`
- Ensure `make` is available
- Delete `.venv/` and rerun `make install`
