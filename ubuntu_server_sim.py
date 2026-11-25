#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ubuntu_server_sim.py - Simulador de Servidor Ubuntu con 3 roles diferenciados
=============================================================================

Roles y comandos disponibles por ventana:
  - server      : admin / luis       -> Comandos de administración (ver todos los logs, gestionar servicios, mapa)
  - operator1   : operador1 / op123  -> Comandos de ataque (scan, exploit, reconocimiento)
  - operator2   : operador2 / op123  -> Comandos de víctima (ver alertas, sus propios logs)

Cada comando mostrado es diferente según el rol. Los comandos básicos del sistema
(pwd, ls, whoami, etc.) están disponibles para todos.

Uso individual:
    python ubuntu_server_sim.py --rol server --usuario admin --password luis --hostname pardoserver
    python ubuntu_server_sim.py --rol operator1 --usuario operador1 --password op123 --hostname op1-endpoint
    python ubuntu_server_sim.py --rol operator2 --usuario operador2 --password op123 --hostname op2-endpoint

Lanzamiento de las 3 ventanas:
    python launch_3_ventanas.py
"""

import argparse
import ctypes
import hashlib
import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Colores tipo terminal (ANSI)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Rutas de C2-DECT
# ---------------------------------------------------------------------------
CS2_ROOT = Path(r"C:\Users\USER1\Desktop\test\cs2")
C2_BASE = CS2_ROOT / "c2-dect"
C2_BUILD = C2_BASE / "build"

# Carpeta de logs compartida entre las 3 ventanas
LOG_DIR = Path("logs")
LOG_SHARED = LOG_DIR / "shared_logs.jsonl"
LOG_ESTADO_RED = LOG_DIR / "estado_red.json"

CREDENCIALES = {
    "server": {"usuario": "admin", "password": "luis", "hostname": "pardoserver", "ip": "192.168.100.10"},
    "operator1": {"usuario": "operador1", "password": "op123", "hostname": "op1-endpoint", "ip": "192.168.100.21"},
    "operator2": {"usuario": "operador2", "password": "op123", "hostname": "op2-endpoint", "ip": "192.168.100.22"},
}

HISTORIAL = []


def ahora_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Índice de comandos básicos del sistema (disponibles para TODOS los roles)
# ---------------------------------------------------------------------------
COMANDOS_BASICOS = {
    "hostnamectl": {
        "win": 'systeminfo | findstr /B /C:"Host Name" /C:"OS Name" /C:"OS Version" /C:"System Manufacturer"',
        "desc": "Información del sistema y hostname",
        "seguro": True,
        "cat": "sistema",
    },
    "hostname": {"win": "hostname", "desc": "Nombre del host", "seguro": True, "cat": "red"},
    "hostname -I": {"win": 'ipconfig | findstr "IPv4"', "desc": "IPs del host (todas las interfaces)", "seguro": True, "cat": "red"},
    "uname -a": {
        "win": 'systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"',
        "desc": "Info del kernel y sistema",
        "seguro": True,
        "cat": "sistema",
    },
    "ip addr": {"win": "ipconfig /all", "desc": "Direcciones IP de interfaces", "seguro": True, "cat": "red"},
    "ip a": {"win": "ipconfig /all", "desc": "IPs de interfaces (alias ip addr)", "seguro": True, "cat": "red"},
    "in a": {"win": "ipconfig /all", "desc": "Alias ip a", "seguro": True, "cat": "red"},
    "in -a": {"win": "ipconfig /all", "desc": "Alias ip -a", "seguro": True, "cat": "red"},
    "ifconfig": {"win": "ipconfig /all", "desc": "Configuración de red", "seguro": True, "cat": "red"},
    "netstat -tulpn": {"win": "netstat -ano", "desc": "Puertos y conexiones activas", "seguro": True, "cat": "red"},
    "ss -tulpn": {"win": "netstat -ano", "desc": "Sockets de red", "seguro": True, "cat": "red"},
    "ping": {"win": "ping", "desc": "Verificar conectividad", "seguro": True, "cat": "red"},
    "smbd --version": {"win": 'sc query smbd && echo "Samba 4.15.13-Ubuntu (simulado)"', "desc": "Versión Samba", "seguro": True, "cat": "servicios"},
    "systemctl": {"win": "sc query", "desc": "Gestionar servicios", "seguro": True, "cat": "servicios"},
    "service": {"win": "sc query", "desc": "Gestionar servicios (SysV)", "seguro": True, "cat": "servicios"},
    "systemctl status": {"win": "sc query", "desc": "Estado de servicio", "seguro": True, "cat": "servicios"},
    "service status": {"win": "sc query", "desc": "Estado de servicio (SysV)", "seguro": True, "cat": "servicios"},
    "journalctl": {"win": "eventvwr", "desc": "Logs del sistema", "seguro": True, "cat": "logs"},
    "dmesg": {"win": "wevtutil qe System /c:10 /f:text", "desc": "Mensajes del kernel", "seguro": True, "cat": "logs"},
    "pwd": {"win": "cd", "desc": "Ruta actual", "seguro": True, "cat": "archivos"},
    "ls": {"win": "dir", "desc": "Listar directorio", "seguro": True, "cat": "archivos"},
    "ls -l": {"win": "dir /q", "desc": "Listar con detalles", "seguro": True, "cat": "archivos"},
    "cat": {"win": "type", "desc": "Mostrar archivo", "seguro": True, "cat": "archivos"},
    "whoami": {"win": "whoami", "desc": "Usuario actual", "seguro": True, "cat": "sistema"},
    "date": {"win": "date /t", "desc": "Fecha", "seguro": True, "cat": "sistema"},
    "uptime": {"win": 'net statistics workstation | findstr "Statistics since"', "desc": "Tiempo de actividad", "seguro": True, "cat": "sistema"},
    "clear": {"win": "cls", "desc": "Limpiar pantalla", "seguro": True, "cat": "consola"},
    "exit": {"win": "exit", "desc": "Salir", "seguro": True, "cat": "consola"},
    "quit": {"win": "exit", "desc": "Salir", "seguro": True, "cat": "consola"},
}

# ---------------------------------------------------------------------------
# Comandos especiales por rol (lo que cada ventana VERÁ en su 'mapa')
# ---------------------------------------------------------------------------
COMANDOS_ESPECIALES_POR_ROL = {
    "server": [
        {"cmd": "mapa", "desc": "Índice de comandos Ubuntu -> Windows", "cat": "consola"},
        {"cmd": "servicios", "desc": "Estado de los 3 servicios del servidor", "cat": "servicios"},
        {"cmd": "status", "desc": "Alias de servicios", "cat": "servicios"},
        {"cmd": "c2", "desc": "Lista de comandos C2-DECT nativos", "cat": "c2"},
        {"cmd": "ver logs", "desc": "Ver TODOS los logs del atacante y la víctima", "cat": "auditoría"},
        {"cmd": "logs", "desc": "Alias de ver logs", "cat": "auditoría"},
        {"cmd": "mapa segmentos", "desc": "Abrir mapa de compromiso en ventana separada", "cat": "red"},
        {"cmd": "mapa red", "desc": "Alias de mapa segmentos", "cat": "red"},
        {"cmd": "clear", "desc": "Limpiar pantalla", "cat": "consola"},
        {"cmd": "exit", "desc": "Salir del simulador", "cat": "consola"},
    ],
    "operator1": [
        {"cmd": "mapa", "desc": "Índice de comandos Ubuntu -> Windows", "cat": "consola"},
        {"cmd": "servicios", "desc": "Estado de los 3 servicios (solo lectura)", "cat": "servicios"},
        {"cmd": "status", "desc": "Alias de servicios", "cat": "servicios"},
        {"cmd": "scan", "desc": "Escanear puertos de un objetivo (reconocimiento)", "cat": "ataque"},
        {"cmd": "exploit", "desc": "Ejecutar exploit simulado contra un objetivo", "cat": "ataque"},
        {"cmd": "ping", "desc": "Verificar conectividad con un objetivo", "cat": "red"},
        {"cmd": "c2", "desc": "Lista de comandos C2-DECT nativos", "cat": "c2"},
        {"cmd": "logs", "desc": "Ver tus propios logs de actividad", "cat": "auditoría"},
        {"cmd": "ver logs", "desc": "Ver tus propios logs de actividad", "cat": "auditoría"},
        {"cmd": "clear", "desc": "Limpiar pantalla", "cat": "consola"},
        {"cmd": "exit", "desc": "Salir del simulador", "cat": "consola"},
    ],
    "operator2": [
        {"cmd": "mapa", "desc": "Índice de comandos Ubuntu -> Windows", "cat": "consola"},
        {"cmd": "servicios", "desc": "Estado de los 3 servicios (solo lectura)", "cat": "servicios"},
        {"cmd": "status", "desc": "Alias de servicios", "cat": "servicios"},
        {"cmd": "alertas", "desc": "Ver alertas de ataques recibidos", "cat": "defensa"},
        {"cmd": "logs", "desc": "Ver tus propios logs de actividad", "cat": "auditoría"},
        {"cmd": "ver logs", "desc": "Ver tus propios logs de actividad", "cat": "auditoría"},
        {"cmd": "c2", "desc": "Lista de comandos C2-DECT nativos", "cat": "c2"},
        {"cmd": "clear", "desc": "Limpiar pantalla", "cat": "consola"},
        {"cmd": "exit", "desc": "Salir del simulador", "cat": "consola"},
    ],
}

ESPECIALES_GLOBALES = ("clear", "exit", "quit")

TIPO2_SERVICIOS = {
    "ssh": "sc query ssh",
    "apache2": "sc query Apache2",
    "smbd": "sc query smbd",
}

# ---------------------------------------------------------------------------
# Comandos C2-DECT (ejecutan sobre carpeta c2-dect)
# ---------------------------------------------------------------------------
C2_COMANDOS = {
    "c2-server": {"cmd": str(C2_BASE / "c2-server.exe"), "desc": "Iniciar servidor C2-DECT", "seguro": False, "cat": "c2"},
    "build-standard-server": {"cmd": 'powershell -ExecutionPolicy Bypass -File "build-standard-server.ps1"', "desc": "Compilar servidor Standard", "seguro": False, "cat": "c2"},
    "build-apt-server": {"cmd": 'powershell -ExecutionPolicy Bypass -File "build-apt-server.ps1"', "desc": "Compilar servidor APT", "seguro": False, "cat": "c2"},
    "build-standard-agent": {"cmd": 'powershell -ExecutionPolicy Bypass -File "build-standard-agent.ps1"', "desc": "Compilar agente Standard", "seguro": False, "cat": "c2"},
    "build-standard-client": {"cmd": 'powershell -ExecutionPolicy Bypass -File "build-standard-client.ps1"', "desc": "Compilar cliente Standard", "seguro": False, "cat": "c2"},
    "build-apt-agent": {"cmd": 'powershell -ExecutionPolicy Bypass -File "build-apt-agent.ps1"', "desc": "Compilar agente APT", "seguro": False, "cat": "c2"},
    "build-apt-client": {"cmd": 'powershell -ExecutionPolicy Bypass -File "build-apt-client.ps1"', "desc": "Compilar cliente APT", "seguro": False, "cat": "c2"},
    "c2-protocol": {"cmd": "go build ./...", "desc": "Compilar protocolo C2", "seguro": True, "cat": "c2"},
    "c2-status": {"cmd": 'type "c2-dect.conf"', "desc": "Configuración C2-DECT", "seguro": True, "cat": "c2"},
    "installer": {"cmd": 'powershell -ExecutionPolicy Bypass -File "installer\\install.ps1"', "desc": "Instalador C2-DECT", "seguro": False, "cat": "c2"},
}

# ---------------------------------------------------------------------------
# Servicios del servidor (simulados, compartidos)
# ---------------------------------------------------------------------------
SERVICIOS = {
    "ssh": {"activo": True, "puerto": 22, "desc": "OpenSSH secure shell server", "win": 'sc query ssh'},
    "apache2": {"activo": True, "puerto": 80, "desc": "Apache HTTP Server", "win": 'sc query Apache2'},
    "smbd": {"activo": True, "puerto": 445, "desc": "Samba SMB Daemon", "win": 'sc query smbd'},
}

# ---------------------------------------------------------------------------
# Sistema de logs compartidos
# ---------------------------------------------------------------------------
def escribir_log_compartido(origen_rol, origen_host, origen_ip, destino, tipo, contenido):
    entrada = {
        "ts": ahora_iso(),
        "origen_rol": origen_rol,
        "origen_host": origen_host,
        "origen_ip": origen_ip,
        "destino": destino,
        "tipo": tipo,
        "contenido": contenido,
        "hash": "",
    }
    entrada["hash"] = sha256_texto(json.dumps(entrada, sort_keys=True))
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_SHARED, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except Exception:
        pass


def leer_logs_compartidos(filtro_rol=None, limite=50):
    logs = []
    if not LOG_SHARED.exists():
        return logs
    try:
        with open(LOG_SHARED, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    entrada = json.loads(linea)
                    if filtro_rol is None or entrada.get("origen_rol") == filtro_rol:
                        logs.append(entrada)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return logs[-limite:]


# ---------------------------------------------------------------------------
# Estado de compromiso de la red
# ---------------------------------------------------------------------------
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


def escribir_estado_red(estado):
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        estado["ultimo_cambio"] = ahora_iso()
        with open(LOG_ESTADO_RED, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def marcar_comprometido(ip, rol_origen, hostname_origen, ip_origen):
    estado = leer_estado_red()
    if ip in estado["segmentos"]:
        estado["segmentos"][ip]["comprometido"] = True
    escribir_estado_red(estado)
    escribir_log_compartido(
        rol_origen, hostname_origen, ip_origen, ip,
        "compromiso", f"{ip} comprometido por {rol_origen}"
    )


# ---------------------------------------------------------------------------
# Salidas formateadas
# ---------------------------------------------------------------------------
def salida_hostnamectl(hostname):
    return "\n".join([
        f"   Static hostname: {hostname}",
        "         Icon name: computer-server",
        "           Chassis: server",
        "      Machine ID: 7a4f92c1e8b34d2a9f1c6d3e5b7a9c2d",
        "    Operating System: Ubuntu 22.04.3 LTS",
        "              Kernel: Linux 5.15.0-101-generic",
        "    Architecture: x86-64",
    ])


def salida_servicios():
    lineas = [f"{C_CYAN}┌─[ SERVICIOS DEL SERVIDOR ]────────────────────────────────────┐{C_RESET}"]
    for nombre, info in SERVICIOS.items():
        estado_txt = f"{C_GREEN}activo (running){C_RESET}" if info["activo"] else f"{C_RED}inactivo (dead){C_RESET}"
        lineas.append(f"  {C_MAGENTA}{nombre}{C_RESET}{' ' * (14 - len(nombre))} │ {estado_txt} │ puerto {C_CYAN}{info['puerto']}{C_RESET} │ {info['desc']}")
    lineas.append(f"{C_CYAN}└───────────────────────────────────────────────────────────────┘{C_RESET}")
    return "\n".join(lineas)


def salida_systemctl_status(servicio: str):
    servicio = servicio.lower()
    if servicio not in SERVICIOS:
        return f"Unit {servicio}.service could not be found."
    info = SERVICIOS[servicio]
    estado = "active (running)" if info["activo"] else "inactive (dead)"
    return (
        f"● {servicio}.service - {info['desc']}\n"
        f"     Loaded: loaded (/lib/systemd/system/{servicio}.service; enabled; vendor preset: enabled)\n"
        f"     Active: {estado}\n"
        f"       Docs: man:{servicio}(8)\n"
        f"    Main PID: {1000 + list(SERVICIOS.keys()).index(servicio)}\n"
        f"        CPU: 0ms\n"
    )


def salida_journalctl(servicio: str = None):
    logs = []
    if servicio == "smbd" or servicio is None:
        logs.append("nov 17 18:10:46 pardoserver systemd[1]: Starting smbd.service - Samba SMB Daemon...")
        logs.append("nov 17 18:10:47 pardoserver systemd[1]: Started smbd.service - Samba SMB Daemon.")
    if servicio == "apache2" or servicio is None:
        logs.append("nov 17 18:11:02 pardoserver systemd[1]: Starting apache2.service - The Apache HTTP Server...")
        logs.append("nov 17 18:11:03 pardoserver systemd[1]: Started apache2.service - The Apache HTTP Server.")
    if servicio == "ssh" or servicio is None:
        logs.append("nov 17 18:11:15 pardoserver systemd[1]: Starting ssh.service - OpenSSH server...")
        logs.append("nov 17 18:11:16 pardoserver systemd[1]: Started ssh.service - OpenSSH server.")
    logs.append("nov 17 18:10:47 pardoserver pardo@pardoserver:~$ sudo systemctl apache2")
    logs.append("sudo: 'systemcli': command not found")
    logs.append("nov 17 18:10:48 pardoserver pardo@pardoserver:~$ sudo systemctl apache2")
    return "\n".join(logs)


def salida_c2_lista():
    lineas = [f"{C_CYAN}┌─[ COMANDOS C2-DECT NATIVOS ]───────────────────────────────────┐{C_RESET}"]
    lineas.append(f"  {'Comando':<24} {'Descripción'}")
    lineas.append(f"{C_DIM}{'-'*70}{C_RESET}")
    for nombre, info in C2_COMANDOS.items():
        seguro_txt = f"{C_GREEN}seguro{C_RESET}" if info["seguro"] else f"{C_RED}cuidado{C_RESET}"
        lineas.append(f"  {C_MAGENTA}{nombre:<24}{C_RESET} {info['desc']} [{seguro_txt}]")
    lineas.append(f"{C_CYAN}└────────────────────────────────────────────────────────────────┘{C_RESET}")
    return "\n".join(lineas)


def salida_mapa_por_rol(rol):
    """Muestra solo los comandos especiales que corresponden a ese rol."""
    comandos = COMANDOS_ESPECIALES_POR_ROL.get(rol, [])
    lineas = [f"{C_CYAN}┌─[ COMANDOS DISPONIBLES PARA SU ROL: {rol.upper()} ]─────────────┐{C_RESET}"]
    lineas.append(f"  {'Comando':<20} {'Descripción'}")
    lineas.append(f"{C_DIM}{'-'*62}{C_RESET}")
    for c in comandos:
        lineas.append(f"  {C_MAGENTA}{c['cmd']:<20}{C_RESET} {c['desc']}")
    lineas.append(f"{C_CYAN}└─────────────────────────────────────────────────────────────────┘{C_RESET}")
    return "\n".join(lineas)


def salida_mapa_segmentos(rol_actual):
    estado = leer_estado_red()
    seg = estado["segmentos"]
    cons = estado["conexiones"]

    lineas = []
    lineas.append(f"{C_CYAN}┌─[ MAPA DE SEGMENTOS DE RED — ESTADO DE COMPROMISO ]─────────────┐{C_RESET}")
    lineas.append(f"{C_DIM}Última actualización: {estado.get('ultimo_cambio', '—')}{C_RESET}")
    lineas.append("")

    lineas.append(f"  {C_WHITE}NODOS:{C_RESET}")
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

        lineas.append(f"    {icono} {C_WHITE}{nombre}{C_RESET} ({C_CYAN}{ip}{C_RESET}) [{C_MAGENTA}{rol}{C_RESET}]")
        lineas.append(f"        Estado: {estado_txt}  |  Servicios: {C_YELLOW}{servicios or 'ninguno'}{C_RESET}")

    lineas.append("")

    lineas.append(f"  {C_WHITE}CONEXIONES:{C_RESET}")
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

        lineas.append(f"    {linea_conn}")

    lineas.append("")

    comprometidos = [ip for ip, d in seg.items() if d["comprometido"]]
    if comprometidos:
        lineas.append(f"  {C_RED}▲ ALERTA: {len(comprometido)} segmento(s) comprometido(s):{C_RESET}")
        for ip in comprometidos:
            lineas.append(f"      - {seg[ip]['nombre']} ({ip})")
    else:
        lineas.append(f"  {C_GREEN}✓ No hay segmentos comprometidos.{C_RESET}")

    lineas.append(f"{C_CYAN}└─────────────────────────────────────────────────────────────────┘{C_RESET}")
    return "\n".join(lineas)


def salida_ver_logs(rol_actual, filtro_rol=None):
    logs = leer_logs_compartidos(filtro_rol=filtro_rol, limite=30)
    if not logs:
        return f"{C_YELLOW}No hay registros de actividad.{C_RESET}"
    lineas = [f"{C_CYAN}┌─[ LOG DE ACTIVIDAD ]───────────────────────────────────────────┐{C_RESET}"]
    lineas.append(f"  {'TS':<20} {'Origen':<18} {'Destino':<12} {'Tipo':<10} {'Contenido'}")
    lineas.append(f"{C_DIM}{'-'*92}{C_RESET}")
    for e in logs:
        ts = e["ts"][:19]
        origen = f"{e['origen_rol']}({e['origen_host']})"
        destino = e["destino"]
        tipo = e["tipo"]
        contenido = e["contenido"][:40]
        lineas.append(f"  {C_WHITE}{ts}{C_RESET} {C_MAGENTA}{origen:<18}{C_RESET} {C_CYAN}{destino:<12}{C_RESET} {C_YELLOW}{tipo:<10}{C_RESET} {contenido}")
    lineas.append(f"{C_CYAN}└─────────────────────────────────────────────────────────────────┘{C_RESET}")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------
def ejecutar_win(comando_win: str, args: str, cwd: Path = None) -> str:
    if not comando_win:
        return ""
    linea = f"{comando_win} {args}".strip()
    try:
        resultado = subprocess.run(
            linea, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=20, cwd=str(cwd) if cwd else None,
        )
        salida = resultado.stdout
        if resultado.stderr:
            salida += f"\n{C_RED}[stderr]{C_RESET} {resultado.stderr.strip()}"
        return salida
    except subprocess.TimeoutExpired:
        return f"{C_YELLOW}[simulador] Comando tardó demasiado.{C_RESET}"
    except Exception as exc:
        return f"{C_RED}[simulador] Error: {exc}{C_RESET}"


def ejecutar_c2(nombre: str, args: str, rol: str, hostname: str, ip: str):
    info = C2_COMANDOS[nombre]
    cmd = info["cmd"]
    seguro = info["seguro"]
    desc = info["desc"]
    linea_completa = f"{cmd} {args}".strip() if args else cmd
    mostrar_servicio(f"c2:{nombre}", linea_completa, desc, "", "ejecutar_real_c2")
    escribir_log_compartido(rol, hostname, ip, "sistema", "comando_c2", f"{nombre} {args}")
    if not seguro:
        print(f"{C_YELLOW}[simulador] Comando C2 no seguro: lanzado en ventana separada.{C_RESET}")
        try:
            subprocess.Popen(linea_completa, shell=True, cwd=str(C2_BASE), creationflags=subprocess.CREATE_NEW_CONSOLE)
            print(f"{C_GREEN}[simulador] Proceso '{nombre}' lanzado.{C_RESET}\n")
        except Exception as exc:
            print(f"{C_RED}[simulador] No se pudo lanzar '{nombre}': {exc}{C_RESET}\n")
        return
    salida = ejecutar_win(cmd, args, cwd=C2_BASE)
    if salida:
        print(salida)
    print()


# ---------------------------------------------------------------------------
# Comandos de ataque / red
# ---------------------------------------------------------------------------
def cmd_scan(objetivo, rol, hostname, ip):
    escribir_log_compartido(rol, hostname, ip, objetivo, "ataque", f"scan {objetivo} - escaneo de puertos simulado")
    if rol == "operator1":
        print(f"{C_RED}[ATAQUE] Escaneando {objetivo}...{C_RESET}")
        print("  Puerto 22 (ssh):    abierto")
        print("  Puerto 80 (http):   abierto")
        print("  Puerto 445 (smbd):  abierto")
        print(f"{C_YELLOW}[simulador] Escaneo completado contra {objetivo}{C_RESET}\n")
    else:
        print(f"{C_YELLOW}[simulador] El comando 'scan' solo está disponible para el atacante (operador1).{C_RESET}\n")


def cmd_exploit(objetivo, rol, hostname, ip):
    escribir_log_compartido(rol, hostname, ip, objetivo, "ataque", f"exploit {objetivo} - explotación simulada")
    if rol == "operator1":
        print(f"{C_RED}[ATAQUE] Ejecutando exploit contra {objetivo}...{C_RESET}")
        print("  CVE-2023-XXXX: intento de desbordamiento de búfer en smbd")
        print("  Resultado: ACCESO OBTENIDO (simulado)")
        print(f"{C_YELLOW}[simulador] Explotación completada contra {objetivo}{C_RESET}\n")
        marcar_comprometido(objetivo, rol, hostname, ip)
        escribir_log_compartido(rol, hostname, ip, objetivo, "alerta", f"Víctima {objetivo} comprometida por {rol}")
    else:
        print(f"{C_YELLOW}[simulador] El comando 'exploit' solo está disponible para el atacante (operador1).{C_RESET}\n")


def cmd_ping_atque(objetivo, rol, hostname, ip):
    escribir_log_compartido(rol, hostname, ip, objetivo, "reconocimiento", f"ping {objetivo}")
    salida = ejecutar_win("ping", objetivo)
    if salida:
        print(salida)


# ---------------------------------------------------------------------------
# Rama de decisión
# ---------------------------------------------------------------------------
def rama_decision(comando: str, seguro: bool) -> str:
    if comando not in COMANDOS_BASICOS and comando not in ESPECIALES_GLOBALES and comando not in C2_COMANDOS:
        # También revisar comandos especiales por rol
        todos_especiales = []
        for cmds in COMANDOS_ESPECIALES_POR_ROL.values():
            for c in cmds:
                todos_especiales.append(c["cmd"])
        if comando not in todos_especiales:
            return "no_encontrado"
    if not seguro:
        return "solo_mostrar_servicio"
    return "ejecutar_real"


# ---------------------------------------------------------------------------
# Interfaz de usuario
# ---------------------------------------------------------------------------
def banner(rol, hostname, ip):
    print(f"{C_CYAN}================================================================{C_RESET}")
    print(f"{C_WHITE}   Servidor Ubuntu 22.04.3 LTS  (simulador indexado a Windows){C_RESET}")
    print(f"{C_WHITE}   Rol       : {C_MAGENTA}{rol}{C_RESET}")
    print(f"{C_WHITE}   Hostname  : {C_MAGENTA}{hostname}{C_RESET}")
    print(f"{C_WHITE}   IP        : {C_CYAN}{ip}{C_RESET}")
    if rol == "operator1":
        print(f"{C_RED}   PERFIL: CLIENTE ATACANTE — comandos: scan, exploit{C_RESET}")
    elif rol == "operator2":
        print(f"{C_RED}   PERFIL: VÍCTIMA — comandos: alertas, ver logs propios{C_RESET}")
    elif rol == "server":
        print(f"{C_GREEN}   PERFIL: SERVIDOR CENTRAL — ve logs de todos, mapa completo{C_RESET}")
    print(f"{C_WHITE}   Servicios : ssh, apache2, smbd | C2-DECT integrado como nativos{C_RESET}")
    print(f"{C_WHITE}   Escribe 'mapa' para ver los comandos de su rol{C_RESET}")
    print(f"{C_CYAN}================================================================{C_RESET}\n")


def prompt(usuario, hostname) -> str:
    return f"{C_GREEN}{usuario}@{hostname}{C_RESET}:{C_BLUE}~{C_RESET}$ "


def mostrar_servicio(comando_ubuntu: str, comando_win: str, desc: str, args: str, rama: str):
    print(f"\n{C_CYAN}╭─[ SERVICIO A HACER ]───────────────────────────────────────────╮{C_RESET}")
    print(f"{C_CYAN}│{C_RESET} Comando Ubuntu : {C_WHITE}{comando_ubuntu}{C_RESET}")
    print(f"{C_CYAN}│{C_RESET} Acción         : {C_WHITE}{desc}{C_RESET}")
    print(f"{C_CYAN}│{C_RESET} Rama (branch)  : {C_MAGENTA}{rama}{C_RESET}")
    print(f"{C_CYAN}│{C_RESET} Ejecutar en Win: {C_YELLOW}{comando_win}{C_RESET} {C_WHITE}{args}{C_RESET}")
    print(f"{C_CYAN}╰────────────────────────────────────────────────────────────────╯{C_RESET}\n")


# ---------------------------------------------------------------------------
# Procesamiento de línea
# ---------------------------------------------------------------------------
def procesar_linea(linea: str, usuario: str, hostname: str, rol: str, ip: str) -> bool:
    linea = linea.strip()
    if not linea:
        return True

    HISTORIAL.append(linea)

    partes = linea.split(None, 1)
    cmd = partes[0].lower()
    args = partes[1] if len(partes) > 1 else ""

    # --- Comandos especiales globales ---
    if cmd == "mapa":
        print(salida_mapa_por_rol(rol))
        return True

    if cmd in ("servicios", "status"):
        print(salida_servicios())
        return True

    if cmd == "c2":
        print(salida_c2_lista())
        return True

    if cmd in ("ver logs", "logs"):
        if rol == "server":
            print(salida_ver_logs(rol))
        else:
            print(salida_ver_logs(rol, filtro_rol=rol))
        return True

    if cmd in ("mapa segmentos", "mapa red"):
        print(f"{C_CYAN}Abriendo mapa de segmentos en ventana separada...{C_RESET}")
        try:
            subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name("mapa_segmentos.py"))],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(Path(__file__).resolve().parent),
            )
            print(f"{C_GREEN}Ventana del mapa abierta.{C_RESET}\n")
        except Exception as exc:
            print(f"{C_RED}No se pudo abrir el mapa: {exc}{C_RESET}\n")
        return True

    if cmd == "clear":
        os.system("cls")
        return True

    if cmd in ("exit", "quit"):
        print(f"{C_YELLOW}Cerrando sesión en {hostname}...{C_RESET}")
        escribir_log_compartido(rol, hostname, ip, "sistema", "sistema", "Sesión cerrada")
        return False

    # --- Comandos de ataque solo para operator1 ---
    if rol == "operator1" and cmd in ("scan", "exploit"):
        objetivo = args if args else "192.168.100.22"
        if cmd == "scan":
            cmd_scan(objetivo, rol, hostname, ip)
        else:
            cmd_exploit(objetivo, rol, hostname, ip)
        return True

    # --- Comando alertas solo para operator2 ---
    if rol == "operator2" and cmd == "alertas":
        print(salida_ver_logs(rol, filtro_rol="operator1"))
        return True

    # --- Comandos básicos de Ubuntu (disponibles para todos) ---
    entrada = None
    cmd_match = cmd
    if cmd in COMANDOS_BASICOS:
        entrada = COMANDOS_BASICOS[cmd]
    else:
        for nombre, info in COMANDOS_BASICOS.items():
            if linea.lower().startswith(nombre + " ") or linea.lower() == nombre:
                entrada = info
                cmd_match = nombre
                args = linea[len(nombre):].strip()
                break

    if entrada is not None:
        win_cmd = entrada["win"]
        desc = entrada["desc"]
        seguro = entrada["seguro"]
        rama = rama_decision(cmd_match, seguro)
        mostrar_servicio(cmd_match, win_cmd or "—", desc, args, rama)

        if rama == "no_encontrado":
            return True

        escribir_log_compartido(rol, hostname, ip, "sistema", "comando", f"{cmd_match} {args}")

        if cmd_match == "hostnamectl":
            print(salida_hostnamectl(hostname))
            return True

        if cmd_match in ("systemctl", "service"):
            if args:
                tokens = args.split()
                sub = tokens[0] if tokens else ""
                objetivo = tokens[-1] if tokens else ""
                if sub == "status" or (cmd_match == "service" and objetivo):
                    print(salida_systemctl_status(objetivo))
                elif sub in ("start", "stop", "restart", "enable", "disable"):
                    nombre_serv = objetivo if objetivo else sub
                    if nombre_serv in SERVICIOS:
                        SERVICIOS[nombre_serv]["activo"] = (sub == "start" or sub == "restart")
                        print(f"{nombre_serv}.service: '{sub}' aplicado (simulado).")
                    else:
                        print(f"Unit {nombre_serv}.service no encontrada.")
                else:
                    print(salida_servicios())
            else:
                print(salida_servicios())
            return True

        if cmd_match == "journalctl":
            objetivo = args if args else None
            print(salida_journalctl(objetivo))
            return True

        if cmd_match == "ping" and rol == "operator1":
            cmd_ping_atque(args, rol, hostname, ip)
            return True

        if not seguro:
            print(f"{C_YELLOW}[simulador] Comando no destructivo simulado: no se ejecutó realmente.{C_RESET}\n")
            return True

        salida_win = ejecutar_win(win_cmd, args)
        if salida_win:
            print(salida_win)
        return True

    # --- Comandos C2-DECT ---
    if cmd in C2_COMANDOS:
        ejecutar_c2(cmd, args, rol, hostname, ip)
        return True
    if cmd == "c2" and args and args.split()[0] in C2_COMANDOS:
        subcmd = args.split()[0]
        subargs = args[len(subcmd):].strip()
        ejecutar_c2(subcmd, subargs, rol, hostname, ip)
        return True

    print(f"{C_RED}bash: {cmd}: orden no encontrada para su rol ({rol}). Use 'mapa' para ver comandos disponibles.{C_RESET}\n")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Simulador Ubuntu con roles diferenciados")
    parser.add_argument("--rol", choices=["server", "operator1", "operator2"], default="server")
    parser.add_argument("--usuario", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--hostname", default=None)
    args = parser.parse_args()

    rol = args.rol
    cred = CREDENCIALES[rol]
    usuario = args.usuario or cred["usuario"]
    password = args.password or cred["password"]
    hostname = args.hostname or cred["hostname"]
    ip = cred["ip"]

    banner(rol, hostname, ip)

    # Pantalla de login
    print(f"\n{C_CYAN}================================================================{C_RESET}")
    print(f"{C_WHITE}         Ubuntu 22.04.3 LTS  {hostname}{C_RESET}")
    print(f"{C_WHITE}         IP : {C_CYAN}{ip}{C_RESET}   Rol : {C_MAGENTA}{rol}{C_RESET}")
    print(f"{C_WHITE}         Acceso restringido{C_RESET}")
    print(f"{C_CYAN}================================================================{C_RESET}\n")

    intentos = 0
    usuario_aut = None
    while intentos < 3:
        usuario = input(f"{C_YELLOW}Login: {C_RESET}").strip()
        password = input(f"{C_YELLOW}Password: {C_RESET}").strip()
        if usuario == cred["usuario"] and password == cred["password"]:
            print(f"{C_GREEN}Acceso concedido. Bienvenido, {usuario}.{C_RESET}\n")
            usuario_aut = usuario
            escribir_log_compartido(rol, hostname, ip, "sistema", "sistema", "Sesión iniciada")
            break
        else:
            intentos += 1
            print(f"{C_RED}Login incorrecto. Intento {intentos}/3{C_RESET}\n")

    if usuario_aut is None:
        print(f"{C_RED}Demasiados intentos fallidos. Acceso denegado.{C_RESET}\n")
        sys.exit(1)

    print(f"{C_DIM}Rol: {rol} | IP: {ip} | Escribe 'mapa' para ver comandos de su rol{C_RESET}\n")

    try:
        while True:
            try:
                linea = input(prompt(usuario_aut, hostname))
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("^C")
                continue
            if not procesar_linea(linea, usuario_aut, hostname, rol, ip):
                break
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
