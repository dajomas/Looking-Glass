## Environment

Run commands from the repository root in a development virtual environment using
the project's supported Python version (Python 3.14). Install the development
requirements; these include the runtime requirements, pytest and httpx:

```sh
python -m pip install -r requirements-dev.txt
```

Node.js is required for the standalone JavaScript regression scripts. These scripts
use Node's built-in modules and do not require a JavaScript package installation.
Keep automated tests isolated from live campaign data. Back up the complete stopped
application data directory before performing manual upgrade or rollback checks.

