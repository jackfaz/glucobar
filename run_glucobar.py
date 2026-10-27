"""Punto d'ingresso per PyInstaller e per l'avvio da sorgente:

    python run_glucobar.py --mode taskbar   (oppure window, tray)
"""

import sys

from glucobar.app import main

if __name__ == "__main__":
    sys.exit(main())
