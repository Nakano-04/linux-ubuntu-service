#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launch_3_ventanas.py - Lanzador de 3 ventanas del simulador Ubuntu
===================================================================

Abre 3 consolas de Windows separadas:
  - Ventana 1: SERVIDOR    (admin / luis)
  - Ventana 2: OPERADOR 1  (operador1 / op123)
  - Ventana 3: OPERADOR 2  (operador2 / op123)

Cada ventana ejecuta ubuntu_server_sim.py con su propio rol y credenciales.

Uso:
    python launch_3_ventanas.py

Requisito: ejecutar desde Windows (usa CREATE_NEW_CONSOLE).
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("ubuntu_server_sim.py")

VENTANAS = [
    {
        "titulo": "SERVIDOR - admin/luis",
        "args": ["--rol", "server", "--usuario", "admin", "--password", "luis", "--hostname", "pardoserver"],
    },
    {
        "titulo": "OPERADOR 1 - operador1/op123",
        "args": ["--rol", "operator1", "--usuario", "operador1", "--password", "op123", "--hostname", "op1-endpoint"],
    },
    {
        "titulo": "OPERADOR 2 - operador2/op123",
        "args": ["--rol", "operator2", "--usuario", "operador2", "--password", "op123", "--hostname", "op2-endpoint"],
    },
]


def main():
    print("Lanzando 3 ventanas del simulador Ubuntu...\n")
    for i, v in enumerate(VENTANAS, start=1):
        cmd = [sys.executable, str(SCRIPT)] + v["args"]
        print(f"  Ventana {i}: {v['titulo']}")
        try:
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(Path(__file__).resolve().parent),
            )
        except Exception as exc:
            print(f"    {exc}")

    print("\nLas 3 ventanas se han abierto. Cada una requiere su login:")
    print("  - SERVIDOR:    admin / luis")
    print("  - OPERADOR 1:  operador1 / op123")
    print("  - OPERADOR 2:  operador2 / op123")


if __name__ == "__main__":
    main()
