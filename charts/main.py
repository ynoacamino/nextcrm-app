#!/usr/bin/env python3
"""Entry point para k6-charts.

Uso:
    python main.py --in <dir_entrada> --out <dir_salida>
    python -m k6_charts --in <dir_entrada> --out <dir_salida>
"""

from k6_charts.cli import main

if __name__ == "__main__":
    main()
