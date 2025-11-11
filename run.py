#!/usr/bin/env python
import os
import subprocess
import sys

# Activate virtual environment and run gunicorn
venv_python = "/app/.venv/bin/python"
if os.path.exists(venv_python):
    # Use virtual environment python
    cmd = [venv_python, "-m", "gunicorn", "app:app", "--bind", f"0.0.0.0:{os.environ.get('PORT', 5000)}"]
else:
    # Fallback to system python
    cmd = [sys.executable, "-m", "gunicorn", "app:app", "--bind", f"0.0.0.0:{os.environ.get('PORT', 5000)}"]

subprocess.run(cmd)