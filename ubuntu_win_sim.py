#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ubuntu_win_sim.py - Simulador de Terminal Ubuntu indexado a Windows
====================================================================

Simula una consola de Ubuntu 22.04 LTS sobre Windows. Cada comando de Linux
que escribas se INDEXA a su equivalente de Windows y se muestra el
"SERVICIO A HACER" (comando real de Windows) antes de ejecutarse.

Diseño detallado:
  - 2 variantes: standard | apt
  - 2 IPs: 192.168.100.10 (servidor C2 central) | 192.168.100.20 (honeypot)
  - 1 servidor central (C2-DECT en IP 1)
  - Rama de decisión (branch): variante + IP destino + comando seguro/no seguro
  - Modo honeypot (solo variante apt + IP 2): captura intentos sin ejecutar
  - Logs forenses JSON con SHA-256

Solo ejecuta comandos de solo lectura (seguros). Los comandos destructivos
solo se muestran como "servicio a hacer", nunca se ejecutan realmente.

Uso:
    python ubuntu_win_sim.py --edition standard --ip 192.168.100.10
    python ubuntu_win_sim.py --edition apt --ip 192.168.100.20 --honeypot

Dentro del simulador:
    mapa        -> muestra el índice completo de comandos indexados
    servicios   -> muestra servicios tipo 2 del sistema
    branch      -> muestra la rama de decisión actual
    clear       -> limpia pantalla
    exit        -> salir

Autor: para C2-DECT (laboratorio / Red Team autorizado)
"""

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import ctypes
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Colores tipo terminal (ANSI) + activación en Windows
# ---------------------------------------------------------------------------
try:
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

C_RESET = "\033[0m"
C_GREEN = "\033[1;32m"   # usuario@host
C_BLUE = "\033[1;34m"    # ruta
C_CYAN = "\033[1;36m"    # servicio a hacer / headers
C_YELLOW = "\033[1;33m"  # advertencias / honeypot
C_RED = "\033[1;31m"     # errores
C_WHITE = "\033[1;37m"   # texto normal
C_DIM = "\033[2;37m"     # comentarios / logs
C_MAGENTA = "\033[1;35m" # variante / rama

# ---------------------------------------------------------------------------
# Constantes de topología (2 IPs + 1 servidor)
# ---------------------------------------------------------------------------
IP_SERVIDOR_C2 = "192.168.100.10"   # IP 1: servidor C2-DECT central (puerto 8443)
IP_HONEYPOT = "192.168.100.20"      # IP 2: honeypot de terminal (solo variante apt)
PUERTO_C2 = 8443

VARIANTES_VALIDAS = ("standard", "apt")

# ---------------------------------------------------------------------------
# Índice de comandos: ubuntu -> {win, desc, seguro, categoria}
# seguro=True  : se ejecuta realmente (solo lectura)
# seguro=False : solo se muestra el "servicio a hacer", NO se ejecuta
# ---------------------------------------------------------------------------
COMANDOS = {
    # --- Solo lectura (seguros, se ejecutan) ---
    "pwd": {"win": "cd", "desc": "Ruta de trabajo actual", "seguro": True, "cat": "sistema"},
    "ls": {"win": "dir", "desc": "Listar contenido del directorio", "seguro": True, "cat": "archivos"},
    "ls -l": {"win": "dir /q", "desc": "Listar con detalles (propietario, tamaño, fecha)", "seguro": True, "cat": "archivos"},
    "ls -a": {"win": "dir /a", "desc": "Listar incluyendo archivos ocultos", "seguro": True, "cat": "archivos"},
    "whoami": {"win": "whoami", "desc": "Usuario actual", "seguro": True, "cat": "sistema"},
    "hostname": {"win": "hostname", "desc": "Nombre del equipo", "seguro": True, "cat": "red"},
    "uname -a": {"win": 'systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"', "desc": "Info del sistema y kernel", "seguro": True, "cat": "sistema"},
    "ver": {"win": "ver", "desc": "Versión del sistema operativo Windows", "seguro": True, "cat": "sistema"},
    "date": {"win": "date /t", "desc": "Fecha actual", "seguro": True, "cat": "sistema"},
    "time": {"win": "time /t", "desc": "Hora actual", "seguro": True, "cat": "sistema"},
    "clear": {"win": "cls", "desc": "Limpiar pantalla", "seguro": True, "cat": "consola"},
    "cat": {"win": "type", "desc": "Mostrar contenido de un archivo", "seguro": True, "cat": "archivos"},
    "type": {"win": "type", "desc": "Mostrar contenido de un archivo (alias Windows)", "seguro": True, "cat": "archivos"},
    "grep": {"win": "findstr", "desc": "Buscar texto dentro de archivos", "seguro": True, "cat": "archivos"},
    "find": {"win": "dir /s /b", "desc": "Buscar archivos en el árbol de directorios", "seguro": True, "cat": "archivos"},
    "ps": {"win": "tasklist", "desc": "Listar procesos en ejecución", "seguro": True, "cat": "procesos"},
    "top": {"win": "tasklist", "desc": "Monitor de procesos (equivalente Windows)", "seguro": True, "cat": "procesos"},
    "tasklist": {"win": "tasklist", "desc": "Listar procesos (nativo Windows)", "seguro": True, "cat": "procesos"},
    "df -h": {"win": "wmic logicaldisk get caption,size,freespace", "desc": "Espacio en disco por unidad", "seguro": True, "cat": "almacenamiento"},
    "df": {"win": "wmic logicaldisk get caption,size,freespace", "desc": "Espacio disponible en unidades", "seguro": True, "cat": "almacenamiento"},
    "free -h": {"win": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory", "desc": "Memoria RAM total y disponible", "seguro": True, "cat": "memoria"},
    "free": {"win": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory", "desc": "Información de memoria", "seguro": True, "cat": "memoria"},
    "ping": {"win": "ping", "desc": "Verificar conectividad de red a un host", "seguro": True, "cat": "red"},
    "ifconfig": {"win": "ipconfig /all", "desc": "Configuración de interfaces de red", "seguro": True, "cat": "red"},
    "ipconfig": {"win": "ipconfig /all", "desc": "Configuración de red (nativo Windows)", "seguro": True, "cat": "red"},
    "netstat": {"win": "netstat -ano", "desc": "Conexiones de red activas y puertos", "seguro": True, "cat": "red"},
    "curl": {"win": "curl", "desc": "Transferir datos desde/a un servidor", "seguro": True, "cat": "red"},
    "echo": {"win": "echo", "desc": "Imprimir texto en pantalla", "seguro": True, "cat": "consola"},
    "history": {"win": "doskey /history", "desc": "Historial de comandos ejecutados", "seguro": True, "cat": "consola"},
    "man": {"win": "help", "desc": "Manual de ayuda de un comando", "seguro": True, "cat": "consola"},
    "help": {"win": "help", "desc": "Ayuda de comandos de Windows", "seguro": True, "cat": "consola"},

    # --- Escritura / destructivos (NO se ejecutan, solo se muestra servicio) ---
    "cd ..": {"win": "cd ..", "desc": "Subir un nivel de directorio", "seguro": True, "cat": "navegacion"},
    "cd /": {"win": "cd \\", "desc": "Ir a la raíz del volumen", "seguro": True, "cat": "navegacion"},
    "cd ~": {"win": "cd %USERPROFILE%", "desc": "Ir al directorio personal", "seguro": True, "cat": "navegacion"},
    "cp": {"win": "copy", "desc": "Copiar archivo o directorio", "seguro": False, "cat": "archivos"},
    "mv": {"win": "move", "desc": "Mover o renombrar archivo o directorio", "seguro": False, "cat": "archivos"},
    "rm": {"win": "del", "desc": "Eliminar un archivo", "seguro": False, "cat": "archivos"},
    "rm -rf": {"win": "rd /s /q", "desc": "Eliminar directorio y contenido recursivamente", "seguro": False, "cat": "archivos"},
    "mkdir": {"win": "md", "desc": "Crear directorio nuevo", "seguro": False, "cat": "archivos"},
    "md": {"win": "md", "desc": "Crear directorio nuevo (alias Windows)", "seguro": False, "cat": "archivos"},
    "rmdir": {"win": "rd", "desc": "Eliminar directorio vacío", "seguro": False, "cat": "archivos"},
    "touch": {"win": "type nul >>", "desc": "Crear archivo vacío o actualizar fecha", "seguro": False, "cat": "archivos"},
    "wget": {"win": "curl -L -o", "desc": "Descargar archivo de la web", "seguro": False, "cat": "red"},
    "apt-get": {"win": "winget install", "desc": "Instalar paquete de software", "seguro": False, "cat": "paquetes"},
    "apt": {"win": "winget", "desc": "Gestor de paquetes (equivalente Windows: winget)", "seguro": False, "cat": "paquetes"},
    "sudo": {"win": "runas /user:Administrador", "desc": "Ejecutar con privilegios de administrador", "seguro": False, "cat": "sistema"},
    "exit": {"win": "exit", "desc": "Salir del simulador", "seguro": True, "cat": "consola"},
    "quit": {"win": "exit", "desc": "Salir del simulador", "seguro": True, "cat": "consola"},
}

# Comandos especiales del simulador (sin equivalente Win directo)
ESPECIALES = ("mapa", "servicios", "branch", "clear", "exit", "quit")

# Servicios tipo 2 del sistema (vista de servicio a hacer)
TIPO2_SERVICIOS = {
    "red": "ipconfig /all",
    "discos": "wmic logicaldisk get caption,size,freespace",
    "memoria": "wmic OS get TotalVisibleMemorySize,FreePhysicalMemory",
    "procesos": "tasklist",
    "servicios": 'sc query type= service state= all',
    "usuarios": "net user",
    "grupos": "net localgroup",
    "hotfixes": "wmic qfe list",
    "arranque": "wmic startup list brief",
    "firewall": "netsh advfirewall show allprofiles",
}

# ---------------------------------------------------------------------------
# Estado del simulador
# ---------------------------------------------------------------------------
HISTORIAL = []
LOGS = []  # entradas forenses en memoria antes de escribir a disco


def ahora_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Rama de decisión (branch)
# ---------------------------------------------------------------------------
def rama_decision(comando: str, variante: str, ip: str, seguro: bool) -> str:
    """
    Devuelve la rama de decisión para un comando dado.
    """
    if comando not in COMANDOS and comando not in ESPECIALES:
        return "no_encontrado"
    if variante not in VARIANTES_VALIDAS:
        return "variante_invalida"
    if variante == "standard":
        return "standard_solo_lectura"
    if ip == IP_HONEYPOT:
        return "honeypot_cebo"
    if not seguro:
        return "solo_mostrar_servicio"
    return "ejecutar_real"


def descripcion_rama(rama: str) -> str:
    map_descr = {
        "no_encontrado": "Comando no reconocido",
        "variante_invalida": "Variante no válida",
        "standard_solo_lectura": "Variante standard: solo comandos de lectura",
        "honeypot_cebo": "Modo honeypot (IP 2): captura sin ejecutar",
        "solo_mostrar_servicio": "Comando destructivo: solo se muestra el servicio a hacer",
        "ejecutar_real": "Comando seguro: se ejecuta el equivalente de Windows",
    }
    return map_descr.get(rama, "Rama desconocida")


# ---------------------------------------------------------------------------
# Ejecución de comandos Windows
# ---------------------------------------------------------------------------
def ejecutar_win(comando_win: str, args: str) -> str:
    if not comando_win:
        return ""
    linea = f"{comando_win} {args}".strip()
    try:
        resultado = subprocess.run(
            linea,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        salida = resultado.stdout
        if resultado.stderr:
            salida += f"\n{C_RED}[stderr]{C_RESET} {resultado.stderr.strip()}"
        return salida
    except subprocess.TimeoutExpired:
        return f"{C_YELLOW}[simulador] Comando tardó demasiado y se detuvo.{C_RESET}"
    except Exception as exc:
        return f"{C_RED}[simulador] Error al ejecutar: {exc}{C_RESET}"


# ---------------------------------------------------------------------------
# Logs forenses
# ---------------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "terminal_sim.log"


def escribir_log_forense(entrada: dict):
    LOGS.append(entrada)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        linea = json.dumps(entrada, ensure_ascii=False)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except Exception as exc:
        print(f"{C_YELLOW}[simulador] No se pudo escribir log forense: {exc}{C_RESET}")


def registrar_entrada(variante, ip, comando, win_cmd, desc, seguro, rama, salida=""):
    entrada = {
        "ts": ahora_iso(),
        "ip": ip,
        "variante": variante,
        "usuario": os.getenv("USERNAME", "usuario"),
        "host": socket.gethostname(),
        "cmd": comando,
        "win": win_cmd or "—",
        "desc": desc,
        "seguro": seguro,
        "rama": rama,
        "descripcion_rama": descripcion_rama(rama),
        "salida": salida.strip()[:2000],  # truncar para no saturar
        "hash": "",
    }
    entrada["hash"] = sha256_texto(json.dumps(entrada, sort_keys=True))
    escribir_log_forense(entrada)
    return entrada


# ---------------------------------------------------------------------------
# Interfaz de usuario (prompt, banner, servicio a hacer)
# ---------------------------------------------------------------------------
def banner(variante: str, ip: str, honeypot: bool):
    print(f"{C_CYAN}================================================================{C_RESET}")
    print(f"{C_WHITE}   Ubuntu 22.04.3 LTS  (simulador indexado a Windows){C_RESET}")
    print(f"{C_WHITE}   Variante : {C_MAGENTA}{variante}{C_RESET}   IP : {C_CYAN}{ip}{C_RESET}")
    if honeypot:
        print(f"{C_YELLOW}   MODO HONEYPOT ACTIVO (captura de comandos, sin ejecución real){C_RESET}")
    print(f"{C_WHITE}   Servidor C2 central : {C_CYAN}{IP_SERVIDOR_C2}:{PUERTO_C2}{C_RESET}")
    print(f"{C_WHITE}   Escribe un comando Linux y verás su equivalente de Windows.{C_RESET}")
    print(f"{C_WHITE}   Comandos especiales: {C_YELLOW}mapa{C_RESET}, {C_YELLOW}servicios{C_RESET}, {C_YELLOW}branch{C_RESET}, {C_YELLOW}clear{C_RESET}, {C_YELLOW}exit{C_RESET}")
    print(f"{C_CYAN}================================================================{C_RESET}\n")


def prompt_ruta(ruta: Path, variante: str, ip: str) -> str:
    usuario = os.getenv("USERNAME", "usuario")
    try:
        host = socket.gethostname()
    except Exception:
        host = "ubuntu"
    perfil = Path(os.getenv("USERPROFILE", str(Path.home())))
    try:
        relativa = ruta.relative_to(perfil)
        mostrar = f"~/{relativa}" if str(relativa) != "." else "~"
    except ValueError:
        mostrar = str(ruta)
    tag_var = f"[{C_MAGENTA}{variante}{C_RESET}]"
    tag_ip = f"[{C_CYAN}{ip}{C_RESET}]"
    return f"{C_GREEN}{usuario}@{host}{C_RESET}{tag_var}{tag_ip}:{C_BLUE}{mostrar}{C_RESET}$ "


def mostrar_servicio(comando_ubuntu: str, comando_win: str, desc: str, args: str, rama: str):
    print(f"\n{C_CYAN}╭─[ SERVICIO A HACER ]───────────────────────────────────────────╮{C_RESET}")
    print(f"{C_CYAN}│{C_RESET} Comando Ubuntu : {C_WHITE}{comando_ubuntu}{C_RESET}")
    print(f"{C_CYAN}│{C_RESET} Acción         : {C_WHITE}{desc}{C_RESET}")
    print(f"{C_CYAN}│{C_RESET} Rama (branch)  : {C_MAGENTA}{rama}{C_RESET} ({descripcion_rama(rama)})")
    print(f"{C_CYAN}│{C_RESET} Ejecutar en Win: {C_YELLOW}{comando_win}{C_RESET} {C_WHITE}{args}{C_RESET}")
    print(f"{C_CYAN}╰────────────────────────────────────────────────────────────────╯{C_RESET}\n")


# ---------------------------------------------------------------------------
# Procesamiento de línea
# ---------------------------------------------------------------------------
def procesar_linea(linea: str, ruta_actual: Path, ctx: dict) -> Path:
    """
    ctx contiene: variante, ip, honeypot, ruta_actual (mutable a través del return)
    Devuelve la nueva ruta_actual.
    """
    variante = ctx["variante"]
    ip = ctx["ip"]
    honeypot = ctx["honeypot"]

    linea = linea.strip()
    if not linea:
        return ruta_actual

    HISTORIAL.append(linea)

    partes = linea.split(None, 1)
    cmd = partes[0].lower()
    args = partes[1] if len(partes) > 1 else ""

    # ---- Comandos especiales del simulador ----
    if cmd == "mapa":
        print(f"\n{C_WHITE}Índice de comandos Ubuntu -> Windows{C_RESET}")
        print(f"{C_DIM}{'-'*72}{C_RESET}")
        print(f"{'Ubuntu':<20} {'Windows':<24} {'Seguro'} {'Categoría'}")
        print(f"{C_DIM}{'-'*72}{C_RESET}")
        for nombre, info in COMANDOS.items():
            win = info["win"] or "—"
            seguro_txt = f"{C_GREEN}SÍ{C_RESET}" if info["seguro"] else f"{C_RED}NO{C_RESET}"
            print(f"{C_GREEN}{nombre:<20}{C_RESET} {C_CYAN}{win:<24}{C_RESET} {seguro_txt}  {info['cat']}")
        print()
        return ruta_actual

    if cmd == "servicios":
        print(f"\n{C_WHITE}Servicios tipo 2 del sistema (vista de servicio a hacer){C_RESET}")
        print(f"{C_DIM}{'-'*72}{C_RESET}")
        for clave, win in TIPO2_SERVICIOS.items():
            print(f"{C_GREEN}{clave:<14}{C_RESET} -> {C_CYAN}{win}{C_RESET}")
        print()
        return ruta_actual

    if cmd == "branch":
        print(f"\n{C_WHITE}Rama de decisión actual{C_RESET}")
        print(f"{C_DIM}{'-'*72}{C_RESET}")
        print(f"  Variante   : {C_MAGENTA}{variante}{C_RESET}")
        print(f"  IP         : {C_CYAN}{ip}{C_RESET}")
        print(f"  Servidor C2: {C_CYAN}{IP_SERVIDOR_C2}:{PUERTO_C2}{C_RESET}")
        print(f"  Honeypot   : {C_YELLOW}{'ACTIVO' if honeypot else 'INACTIVO'}{C_RESET}")
        print()
        return ruta_actual

    if cmd == "clear":
        os.system("cls")
        return ruta_actual

    if cmd in ("exit", "quit"):
        print(f"{C_YELLOW}Saliendo del simulador Ubuntu...{C_RESET}")
        sys.exit(0)

    # ---- Buscar comando en índice ----
    entrada = None
    cmd_match = cmd
    if cmd in COMANDOS:
        entrada = COMANDOS[cmd]
    else:
        # búsqueda por prefijo (ej. "ls -l")
        for nombre, info in COMANDOS.items():
            if linea.lower().startswith(nombre + " ") or linea.lower() == nombre:
                entrada = info
                cmd_match = nombre
                args = linea[len(nombre):].strip()
                break

    if entrada is None:
        print(f"{C_RED}bash: {cmd}: orden no encontrada (use 'mapa' para ver comandos){C_RESET}\n")
        registrar_entrada(variante, ip, linea, "—", "Comando no encontrado", False, "no_encontrado")
        return ruta_actual

    win_cmd = entrada["win"]
    desc = entrada["desc"]
    seguro = entrada["seguro"]

    # Evaluar rama de decisión
    rama = rama_decision(cmd_match, variante, ip, seguro)

    # Mostrar SIEMPRE el servicio a hacer
    mostrar_servicio(cmd_match, win_cmd or "—", desc, args, rama)

    # Registrar entrada forense (incluso si no se ejecuta)
    salida_ejecucion = ""

    if rama == "no_encontrado":
        print(f"{C_RED}Comando no reconocido.{C_RESET}\n")
        return ruta_actual

    if rama in ("standard_solo_lectura", "honeypot_cebo", "solo_mostrar_servicio"):
        if not seguro:
            print(f"{C_YELLOW}[simulador] Comando no destructivo simulado: no se ejecutó realmente en Windows.{C_RESET}\n")
        else:
            # seguro pero en standard o honeypot -> solo lectura permitida, se ejecuta
            salida_ejecucion = ejecutar_win(win_cmd, args)
            if salida_ejecucion:
                print(salida_ejecucion)
            print()

    elif rama == "ejecutar_real":
        salida_ejecucion = ejecutar_win(win_cmd, args)
        if salida_ejecucion:
            print(salida_ejecucion)
        print()

    registrar_entrada(variante, ip, cmd_match, win_cmd, desc, seguro, rama, salida_ejecucion)

    # ---- Manejo de cambio de directorio (simulado) ----
    if cmd_match == "cd" and args:
        destino = args
        if destino == "..":
            ruta_actual = ruta_actual.parent
        elif destino in ("~", "%USERPROFILE%"):
            ruta_actual = Path(os.getenv("USERPROFILE", str(Path.home())))
        elif destino == "\\":
            ruta_actual = Path(ruta_actual.anchor)
        else:
            nuevo = (ruta_actual / destino).resolve()
            if nuevo.exists() and nuevo.is_dir():
                ruta_actual = nuevo
            else:
                print(f"{C_RED}bash: cd: {destino}: No existe el archivo o el directorio{C_RESET}\n")

    return ruta_actual


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Simulador de terminal Ubuntu indexado a Windows"
    )
    parser.add_argument(
        "--edition", "--edicion",
        choices=VARIANTES_VALIDAS,
        default="standard",
        help="Variante: standard o apt (default: standard)",
    )
    parser.add_argument(
        "--ip",
        choices=[IP_SERVIDOR_C2, IP_HONEYPOT],
        default=IP_SERVIDOR_C2,
        help=f"IP destino: {IP_SERVIDOR_C2} (servidor C2) o {IP_HONEYPOT} (honeypot)",
    )
    parser.add_argument(
        "--honeypot",
        action="store_true",
        help="Activar modo honeypot (solo tiene efecto con --edition apt --ip 192.168.100.20)",
    )
    args = parser.parse_args()

    variante = args.edition
    ip = args.ip
    honeypot = args.honeypot and (variante == "apt") and (ip == IP_HONEYPOT)

    ctx = {"variante": variante, "ip": ip, "honeypot": honeypot}

    banner(variante, ip, honeypot)
    ruta_actual = Path.cwd()
    print(f"{C_DIM}Directorio de trabajo: {ruta_actual}{C_RESET}")
    print(f"{C_DIM}Servidor C2 central : {IP_SERVIDOR_C2}:{PUERTO_C2}{C_RESET}\n")

    try:
        while True:
            try:
                linea = input(prompt_ruta(ruta_actual, variante, ip))
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("^C")
                continue
            ruta_actual = procesar_linea(linea, ruta_actual, ctx)
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
