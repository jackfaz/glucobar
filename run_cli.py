"""Punto d'ingresso del comando da terminale (glucobar-cli.exe):

    python run_cli.py setup
"""

import sys

from glucobar.cli import main

if __name__ == "__main__":
    sys.exit(main())
