## Resume locally

```bash
git clone https://github.com/dajomas/Looking-Glass.git
cd Looking-Glass
git switch features/perplexity
git status --short --branch
git log -5 --oneline
```

For an existing checkout, inspect status and local commits before fetching/integrating remote changes. Do not discard uncommitted work.

The live README documents this basic setup:

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
# Optional: copy only if config.yaml does not already exist.
cp config.example.yaml config.yaml
.venv/bin/python python/main.py
```

First startup creates a superadmin and logs an initial password, unless LG_SUPERADMIN_PASSWORD was supplied for initialization. Change the initial password. Never commit credentials, local configuration containing secrets, database files, uploaded maps or session data.

The live README documents this basic test invocation:

```bash
.venv/bin/pip install -r requirements-dev.txt
cd python
../.venv/bin/python -m pytest -q
```

Read docs/testing.md before browser tests. The live README references Playwright lifecycle constraints, Rocky Linux/WSL font/rendering preflight and python/tests/check_browser_environment.py. Inspect runtests.sh and other launcher scripts before relying on their behavior. Record actual commands, results and limitations; do not describe collection or setup-plan checks as passing browser execution.

