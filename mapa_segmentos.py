#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mapa_segmentos.py - Mapa de segmentos de red en ventana separada
=================================================================

Muestra el estado de compromiso de los segmentos de red (servidor, atacante, víctima).
Se ejecuta en su propia consola de Windows.

Uso:
    python mapa_segmentos.py

Lee los datos de logs/estado_red.json (compartido con ubuntu_server_sim.py).
"""

import json
import os
import sys
import ctypes
from pathlib import Path
from datetime import datetime, timezone

# Colores ANSI
try:
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

C_RESET = "\033[0m"
C_GREEN = "\033[1;32m"
C_BLUE = "\033[1;34m"
C_CYAN = "\033[1;36m"
C_YELLOW = "\033[1;33m"
C_RED = "\033[1;31m"
C_WHITE = "\033[1;37m"
C_DIM = "\033[2;37m"
C_MAGENTA = "\033[1;35m"

LOG_DIR = Path("logs")
LOG_ESTADO_RED = LOG_DIR / "estado_red.json"


def ahora_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def leer_estado_red():
    estado_default = {
        "segmentos": {
            "192.168.100.10": {"nombre": "pardoserver", "rol": "servidor", "comprometido": False, "servicios": ["ssh:22", "apache2:80", "smbd:445"]},
            "192.168.100.21": {"nombre": "op1-endpoint", "rol": "atacante", "comprometido": False, "servicios": []},
            "192.168.100.22": {"nombre": "op2-endpoint", "rol": "víctima", "comprometido": False, "servicios": []},
        },
        "conexiones": [
            {"origen": "192.168.100.21", "destino": "192.168.100.10", "tipo": "admin"},
            {"origen": "192.168.100.21", "destino": "192.168.100.22", "tipo": "ataque"},
            {"origen": "192.168.100.22", "destino": "192.168.100.10", "tipo": "monitoreo"},
        ],
        "ultimo_cambio": ahora_iso(),
    }
    if not LOG_ESTADO_RED.exists():
        return estado_default
    try:
        with open(LOG_ESTADO_RED, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return estado_default


def main():
    print(f"\n{C_CYAN}╔═══════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_WHITE}         MAPA DE SEGMENTOS DE RED — ESTADO DE COMPROMISO{C_RESET}")
    print(f"{C_CYAN}╚═══════════════════════════════════════════════════════════════════╝{C_RESET}\n")

    estado = leer_estado_red()
    seg = estado["segmentos"]
    cons = estado["conexiones"]

    print(f"{C_DIM}Última actualización: {estado.get('ultimo_cambio', '—')}{C_RESET}\n")

    # Nodos
    print(f"{C_WHITE}  NODOS:{C_RESET}")
    for ip, datos in seg.items():
        nombre = datos["nombre"]
        rol = datos["rol"]
        comprometido = datos["comprometido"]
        servicios = ", ".join(datos.get("servicios", []))

        if comprometido:
            estado_txt = f"{C_RED}COMPROMETIDO{C_RESET}"
            icono = "☠"
        elif rol == "servidor":
            estado_txt = f"{C_GREEN}SEGURO{C_RESET}"
            icono = "🖥"
        elif rol == "atacante":
            estado_txt = f"{C_YELLOW}ATACANTE{C_RESET}"
            icono = "💻"
        else:
            estado_txt = f"{C_GREEN}SEGURO{C_RESET}"
            icono = "💻"

        print(f"    {icono} {C_WHITE}{nombre}{C_RESET} ({C_CYAN}{ip}{C_RESET}) [{C_MAGENTA}{rol}{C_RESET}]")
        print(f"        Estado: {estado_txt}  |  Servicios: {C_YELLOW}{servicios or 'ninguno'}{C_RESET}")

    print()

    # Conexiones
    print(f"{C_WHITE}  CONEXIONES:{C_RESET}")
    for c in cons:
        origen_ip = c["origen"]
        destino_ip = c["destino"]
        tipo = c["tipo"]

        origen_datos = seg.get(origen_ip, {})
        destino_datos = seg.get(destino_ip, {})
        origen_nom = origen_datos.get("nombre", origen_ip)
        destino_nom = destino_datos.get("nombre", destino_ip)
        destino_comp = destino_datos.get("comprometido", False)

        if tipo == "ataque" and destino_comp:
            linea_conn = f"{C_RED}✗ {origen_nom} → {destino_nom} [ATAQUE — ÉXITO: COMPROMETIDO]{C_RESET}"
        elif tipo == "ataque":
            linea_conn = f"{C_YELLOW}⚠ {origen_nom} → {destino_nom} [ATAQUE — INTENTO]{C_RESET}"
        else:
            linea_conn = f"{C_CYAN}─ {origen_nom} → {destino_nom} [{tipo}]{C_RESET}"

        print(f"    {linea_conn}")

    print()

    # Resumen
    comprometidos = [ip for ip, d in seg.items() if d["comprometido"]]
    if comprometidos:
        print(f"{C_RED}  ▲ ALERTA: {len(comprometido)} segmento(s) comprometido(s):{C_RESET}")
        for ip in comprometidos:
            print(f"      - {seg[ip]['nombre']} ({ip})")
    else:
        print(f"{C_GREEN}  ✓ No hay segmentos comprometidos.{C_RESET}")

    print(f"\n{C_CYAN}═════════════════════════════════════════════════════════════════════{C_RESET}\n")
    input(f"{C_YELLOW}Presiona Enter para cerrar esta ventana...{C_RESET}")


if __name__ == "__main__":
    main()
