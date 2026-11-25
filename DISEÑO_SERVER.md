# Diseño: Simulador de Servidor Ubuntu — 3 Roles (Servidor + Atacante + Víctima)

> Proyecto: C2-DECT v3.6.1  
> Carpeta: `C:\Users\USER1\Desktop\test\cs2\linux ubuntu service\`  
> Archivos: `ubuntu_server_sim.py`, `launch_3_ventanas.py`  
> Estado: Implementado (laboratorio / Red Team autorizado)

---

## 1 · Visión general

Simulador de **servidor Ubuntu 22.04 LTS** que se ejecuta en **3 consolas de Windows separadas**.
Cada ventana tiene un rol distinto en un escenario de seguridad:

| Ventana | Rol | Login (por defecto) | Hostname | IP simulada | Función |
|---------|-----|---------------------|----------|-------------|---------|
| 1 | **Servidor** | `admin` / `luis` | `pardoserver` | `192.168.100.10` | Centraliza y muestra logs de todos |
| 2 | **Operador 1** | `operador1` / `op123` | `op1-endpoint` | `192.168.100.21` | **Cliente atacante** (scan, exploit) |
| 3 | **Operador 2** | `operador2` / `op123` | `op2-endpoint` | `192.168.100.22` | **Víctima** (recibe ataques, registra alertas, ve alertas) |
| 4 (opcional) | **Mapa de Segmentos** | — | — | — | Ventana separada que dibuja el estado de compromiso |

Cada comando de Ubuntu se **indexa (mapea)** a su equivalente de Windows y se muestra el **"servicio a hacer"** antes de ejecutarse.

Además, los comandos del proyecto **C2-DECT** están integrados como si fueran nativos del sistema operativo simulado (`c2-server`, `build-*`, `c2-protocol`, `installer`, etc.).

---

## 2 · Topología (3 ventanas)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    3 CONSOLAS DE WINDOWS (procesos independientes)          │
├─────────────────┬───────────────────────┬───────────────────────────────────┤
│  VENTANA 1      │  VENTANA 2            │  VENTANA 3                        │
│  ┌───────────┐  │  ┌────────────────┐   │  ┌────────────────┐              │
│  │ SERVIDOR  │  │  │ OPERADOR 1     │   │  │ OPERADOR 2     │              │
│  │ admin/luis│  │  │ operador1/op123│   │  │ operador2/op123│              │
│  │ pardoserver│ │  │ op1-endpoint   │   │  │ op2-endpoint   │              │
│  │ 192.168...│  │  │ 192.168.100.21 │   │  │ 192.168.100.22 │              │
│  │           │  │  PERFIL: ATACANTE│   │  │ PERFIL: VÍCTIMA│              │
│  │ Logs: TODOS│  │  scan, exploit │   │  │ alertas recibidas│              │
│  └───────────┘  │  └────────────────┘   │  └────────────────┘              │
│      ▲          │                       │                                   │
│      │          │                       │                                   │
│      └────Logs compartidos─────────────┘                                   │
│              (logs/shared_logs.jsonl)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3 · Los 3 servicios del servidor (simulados)

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `ssh` | 22 | OpenSSH secure shell server |
| `apache2` | 80 | Apache HTTP Server |
| `smbd` | 445 | Samba SMB Daemon |

Consultar con: `systemctl status <servicio>`, `service <servicio> status`, `servicios`.

---

## 4 · Login por ventana

Cada ventana pide sus propias credenciales antes de mostrar el prompt:

```
VENTANA 1 (Servidor):
Login: admin
Password: luis
Acceso concedido. Bienvenido, admin.
admin@pardoserver:~$

VENTANA 2 (Atacante):
Login: operador1
Password: op123
Acceso concedido. Bienvenido, operador1.
operador1@op1-endpoint:~$

VENTANA 3 (Víctima):
Login: operador2
Password: op123
Acceso concedido. Bienvenido, operador2.
operador2@op2-endpoint:~$
```

Máximo 3 intentos. Tras el fallo, acceso denegado.

---

## 5 · Comandos de ataque y red (escenario ofensivo / defensivo)

Disponibles según el rol:

### Desde Operador 1 (Atacante)
| Comando | Efecto |
|---------|--------|
| `scan <ip>` | Escanea puertos del objetivo (simulado). Registra log de ataque. |
| `exploit <ip>` | Ejecuta exploit simulado contra el objetivo. Registra compromiso y alerta. |
| `ping <ip>` | Ping normal + registro de reconocimiento en logs. |

### Desde Operador 2 (Víctima)
| Comando | Efecto |
|---------|--------|
| `alertas` | Muestra los ataques recibidos desde operator1 (logs filtrados por origen). |

### Desde Servidor (admin/luis)
| Comando | Efecto |
|---------|--------|
| `ver logs` | Muestra **todos** los logs del atacante y de la víctima (auditoría central). |

---

## 6 · Sistema de logs compartidos

Todas las acciones se escriben en `logs/shared_logs.jsonl` (formato JSON, una línea por entrada):

```json
{"ts":"2026-11-17T18:10:46Z","origen_rol":"operator1","origen_host":"op1-endpoint",
 "origen_ip":"192.168.100.21","destino":"192.168.100.22","tipo":"ataque",
 "contenido":"scan 192.168.100.22 - escaneo de puertos simulado","hash":"a3f1..."}
```

Campos:
- `ts`: timestamp UTC
- `origen_rol`, `origen_host`, `origen_ip`: quién generó el evento
- `destino`: objetivo del evento (servicio, IP, sistema)
- `tipo`: comando, ataque, alerta, reconocimiento, sistema
- `contenido`: descripción del evento
- `hash`: SHA-256 truncado para integridad

El servidor puede leer todos los logs. Los operadores solo ven los suyos propios (o las alertas dirigidas a ellos).

---

## 7 · Mapa de Segmentos de Red (ventana separada)

El simulador incluye un **mapa de segmentos** que se abre en su propia ventana de Windows
(`mapa_segmentos.py`). Muestra el estado de compromiso de cada segmento en tiempo real.

### Cómo abrirlo
Desde cualquiera de las 3 ventanas, escribe:
```
mapa segmentos
```
o
```
mapa red
```

Esto lanzará `mapa_segmentos.py` en una **consola de Windows separada** (`CREATE_NEW_CONSOLE`).

### Estado de compromiso

| Segmento | IP | Rol | Estado inicial | Cuando se compromete |
|----------|-----|-----|----------------|---------------------|
| Servidor | `192.168.100.10` | servidor | SEGURO | Nunca (en este escenario) |
| Atacante | `192.168.100.21` | atacante | ATACANTE | N/A |
| Víctima | `192.168.100.22` | víctima | SEGURO | Cuando `exploit` tiene éxito |

### Flujo de compromiso

1. El **atacante** ejecuta `exploit 192.168.100.22` desde operator1.
2. El simulador marca a `192.168.100.22` (op2-endpoint) como **COMPROMETIDO** en `logs/estado_red.json`.
3. Se registra un log de tipo `compromiso` en `logs/shared_logs.jsonl`.
4. El mapa de segmentos muestra la víctima con icono `☠` y estado `COMPROMETIDO` en rojo.
5. La conexión atacante → víctima cambia de `[ATAQUE — INTENTO]` a `[ATAQUE — ÉXITO: COMPROMETIDO]`.

### Ejemplo de salida del mapa

```
╔════════════════════════════════════════════════════════════════════╗
         MAPA DE SEGMENTOS DE RED — ESTADO DE COMPROMISO
╚════════════════════════════════════════════════════════════════════╝

Última actualización: 2026-11-17T18:15:30Z

  NODOS:
    🖥 pardoserver (192.168.100.10) [servidor]
        Estado: SEGURO  |  Servicios: ssh:22, apache2:80, smbd:445

    💻 op1-endpoint (192.168.100.21) [atacante]
        Estado: ATACANTE  |  Servicios: ninguno

    ☠ op2-endpoint (192.168.100.22) [víctima]
        Estado: COMPROMETIDO  |  Servicios: ninguno

  CONEXIONES:
    ─ pardoserver → op1-endpoint [admin]
    ✗ op1-endpoint → op2-endpoint [ATAQUE — ÉXITO: COMPROMETIDO]
    ─ op2-endpoint → pardoserver [monitoreo]

  ▲ ALERTA: 1 segmento(s) comprometido(s):
      - op2-endpoint (192.168.100.22)

═════════════════════════════════════════════════════════════════════
```

---

## 8 · Índice de comandos Ubuntu → Windows (seleccionado)

Comando Ubuntu | Equivalente Windows | Descripción | Seguro
---|---|---|---
`hostnamectl` | `systeminfo \| findstr ...` | Info del sistema | ✅
`hostname` | `hostname` | Nombre del host | ✅
`hostname -I` | `ipconfig \| findstr "IPv4"` | IPs del host | ✅
`ip addr` / `ip a` / `in a` / `in -a` | `ipconfig /all` | Direcciones IP de interfaces | ✅
`ifconfig` | `ipconfig /all` | Configuración de red | ✅
`netstat -tulpn` / `ss -tulpn` | `netstat -ano` | Puertos y conexiones | ✅
`ping` | `ping` | Conectividad | ✅
`smbd --version` | `sc query smbd && echo "Samba ..."` | Versión Samba | ✅
`systemctl` / `service` | `sc query` | Gestionar servicios | ✅
`ls` / `ls -l` | `dir` / `dir /q` | Listar directorio | ✅
`cat` | `type` | Mostrar archivo | ✅
`whoami` | `whoami` | Usuario actual | ✅
`date` | `date /t` | Fecha | ✅
`clear` | `cls` | Limpiar pantalla | ✅
`exit` / `quit` | `exit` | Salir | ✅

---

## 8 · Comandos C2-DECT como nativos del SO

Desde cualquier ventana se pueden ejecutar herramientas de C2-DECT como si fueran comandos del sistema:

| Comando | Efecto |
|---------|--------|
| `c2-server` | Inicia `c2-server.exe` (ventana separada) |
| `build-standard-server` | Compila servidor Standard (PowerShell) |
| `build-apt-server` | Compila servidor APT (PowerShell) |
| `build-standard-agent` | Compila agente Standard |
| `build-standard-client` | Compila cliente GUI Standard |
| `build-apt-agent` | Compila agente APT |
| `build-apt-client` | Compila cliente GUI APT |
| `c2-protocol` | `go build ./...` en c2-protocol |
| `c2-status` | Muestra `c2-dect.conf` |
| `installer` | Ejecuta instalador de C2-DECT |

Los comandos "no seguros" (builds, servidor, instalador) se lanzan en una **ventana de Windows separada** (`CREATE_NEW_CONSOLE`) para no bloquear el simulador.

---

## 9 · Rama de decisión (branch)

```
INICIO: operador escribe comando (tras login)
        │
        ▼
┌─────────────────────┐
│ ¿Comando conocido?  ├─ No ──► "orden no encontrada"
└──────────┬──────────┘
           │ Sí
           ▼
┌─────────────────────┐
│ ¿Comando seguro?    ├─ No ──► mostrar servicio + lanzar en 2da ventana (si es C2)
└──────────┬──────────┘
           │ Sí
           ▼
┌─────────────────────┐
│ ¿Es comando servidor?├─ Sí ──► simular (hostnamectl, systemctl, journalctl)
└──────────┬──────────┘
           │ No
           ▼
    Ejecutar equivalente de Windows
           │
           ▼
    Escribir log compartido (origen, destino, tipo, hash)
           │
           ▼
    Mostrar salida al usuario
```

---

## 10 · Ejemplo de sesión completa

**Ventana 2 (Atacante):**
```
operador1@op1-endpoint:~$ scan 192.168.100.22

╭─[ SERVICIO A HACER ]───────────────────────────────────────────╮
│ Comando Ubuntu : scan                                          │
│ Acción         : Escaneo de puertos del objetivo               │
│ Rama (branch)  : ataque                                        │
╰────────────────────────────────────────────────────────────────╯

[ATAQUE] Escaneando 192.168.100.22...
  Puerto 22 (ssh):    abierto
  Puerto 80 (http):   abierto
  Puerto 445 (smbd):  abierto
[simulador] Escaneo completado contra 192.168.100.22
```

**Ventana 3 (Víctima):**
```
operador2@op2-endpoint:~$ alertas

┌─[ LOG DE ACTIVIDAD ]───────────────────────────────────────────┐
  2026-11-17T18:10:46 operator1(op1-endpoint) 192.168.100.22  ataque   scan 192.168.100.22...
└─────────────────────────────────────────────────────────────────┘
```

**Ventana 1 (Servidor):**
```
admin@pardoserver:~$ ver logs

┌─[ LOG DE ACTIVIDAD ]───────────────────────────────────────────┐
  2026-11-17T18:10:46 operator1(op1-endpoint) 192.168.100.22  ataque   scan 192.168.100.22...
  2026-11-17T18:10:48 operator1(op1-endpoint) 192.168.100.22  ataque   exploit 192.168.100.22...
└─────────────────────────────────────────────────────────────────┘
```

---

## 11 · Cómo lanzar

```powershell
# Desde la carpeta linux ubuntu service:
python launch_3_ventanas.py
```

Esto abre 3 consolas de Windows simultáneas. Luego hacer login en cada una:

| Ventana | Usuario | Password |
|---------|---------|----------|
| Servidor | `admin` | `luis` |
| Operador 1 (Atacante) | `operador1` | `op123` |
| Operador 2 (Víctima) | `operador2` | `op123` |

---

## 12 · Archivos entregables

| Archivo | Propósito |
|---------|-----------|
| `ubuntu_server_sim.py` | Simulador con 3 roles, logs compartidos, comandos de ataque y C2-DECT nativos |
| `launch_3_ventanas.py` | Lanzador de las 3 consolas de Windows |
| `mapa_segmentos.py` | Mapa de compromiso en ventana separada |
| `logs/shared_logs.jsonl` | Log de auditoría compartido (generado en runtime) |
| `logs/estado_red.json` | Estado de compromiso de segmentos (generado en runtime) |
| `DISEÑO_SERVER.md` | Este documento de diseño |

---

> **Recordatorio de uso:** Uso exclusivo para testing de seguridad autorizado, operaciones de Red Team y laboratorios de detección con alcance declarado. No operar contra activos de terceros sin autorización escrita vigente.
