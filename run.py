#!/usr/bin/env python3
"""
Entry point para ejecutar el simulador de atterrizaje lunar.
"""

import sys
from pathlib import Path

# Agregar src al path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import App

if __name__ == "__main__":
    app = App()
    app.run()
