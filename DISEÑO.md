# Diseño: Simulador de Terminal Ubuntu indexado a Windows — "linux ubuntu service"

> Proyecto: C2-DECT v3.6.1  
> Carpeta: `C:\Users\USER1\Desktop\test\cs2\linux ubuntu service\`  
> Archivo principal: `ubuntu_win_sim.py`  
> Estado: Propuesta de implementación (laboratorio / Red Team autorizado)

---

## 1 · Visión general

Se construye un **simulador de terminal Ubuntu 22.04 LTS** que corre sobre Windows.
Cada comando de Linux que escribe el operador se **indexa (mapea)** a su equivalente de
Windows y, **antes de ejecutarse, se muestra el "servicio a hacer"** (el comando real
de Windows que se dispararía).

El diseño contempla:

| Elemento | Especificación |
|----------|----------------|
| **Variantes** | 2 (standard y apt) |
| **IPs** | 2 (1 para servidor C2, 1 para honeypot terminal) |
| **Servidor** | 1 central (C2-DECT servidor) |
| **Ramificación** | Sí: rama de decisión según variante, IP y tipo de comando |
| **Honeypot** | Sí (solo variante apt + IP 2) |
| **Logs forenses** | Sí (JSON por línea con SHA-256) |

---

## 2 · Topología de red (2 IPs + 1 servidor)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RED DE LABORATORIO                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Operador]                                                         │
│     │                                                                │
│     ▼                                                                │
│  ┌─────────────────┐    (IP 1: 192.168.100.10)    ┌──────────────┐ │
│  │ TERMINAL UBUNTU │────────────────────────────►│ SERVIDOR     │ │
│  │ SIMULADOR       │    Win: "servicio a hacer"   │ C2-DECT      │ │
│  │ (standard/apt)  │                              │ (1 servidor) │ │
│  └─────────────────┘                              │ puerto 8443  │ │
│     │                                             └──────┬───────┘ │
│     │ (IP 2: 192.168.100.20)                             │           │
│     ▼                                                    ▼           │
│  ┌─────────────────┐                        ┌──────────────┐        │
│  │ HONEYPOT        │◄───────────────────────│ TRÁFICO      │        │
│  │ TERMINAL        │    simula servicios    │ DE CEBO      │        │
│  │ (apt + IP 2)    │    indexado a Windows  │ (captura)    │        │
│  └─────────────────┘                        └──────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

- **IP 1 (192.168.100.10)**: Servidor C2-DECT central. Aquí reciben check-in los
  agentes y el operador ejecuta comandos reales.
- **IP 2 (192.168.100.20)**: Honeypot de terminal. Simula un Ubuntu real para atraer
  y registrar intentos de intrusión.

---

## 3 · Las 2 variantes

Consistente con C2-DECT (§3 del README), el simulador tiene dos ediciones:

| Capacidad | standard | apt |
|-----------|----------|-----|
| Comandos solo lectura (`pwd`, `ls`, `whoami`, `ps`, `ping`, `ipconfig`) | ✅ se ejecutan | ✅ se ejecutan |
| Comandos de escritura (`cp`, `mv`, `rm`, `mkdir`, `touch`, `wget`, `apt`, `sudo`) | ⚠️ solo se muestra el servicio | ⚠️ solo se muestra el servicio |
| Honeypot terminal integrado | ❌ No | ✅ Sí (sobre IP 2) |
| Registro forense de comandos | Básico | Completo (hash, timestamp, IP origen) |
| "Servicio a hacer" extendido | Básico | Con rama de decisión y categoría |

---

## 4 · Índice de comandos Ubuntu → Windows (detallado)

Comando Ubuntu | Comando Windows ("servicio a hacer") | Descripción | ¿Se ejecuta? | Categoría
--- | --- | --- | --- | ---
`pwd` | `cd` | Ruta actual | ✅ | sistema
`ls` | `dir` | Listar directorio | ✅ | archivos
`ls -l` | `dir /q` | Listar con detalles | ✅ | archivos
`ls -a` | `dir /a` | Incluir ocultos | ✅ | archivos
`whoami` | `whoami` | Usuario actual | ✅ | sistema
`hostname` | `hostname` | Nombre del equipo | ✅ | red
`uname -a` | `systeminfo \| findstr ...` | Info del sistema | ✅ | sistema
`ver` | `ver` | Versión Windows | ✅ | sistema
`date` | `date /t` | Fecha | ✅ | sistema
`time` | `time /t` | Hora | ✅ | sistema
`clear` | `cls` | Limpiar pantalla | ✅ | consola
`cat archivo` | `type archivo` | Mostrar archivo | ✅ | archivos
`grep patrón archivo` | `findstr patrón archivo` | Buscar texto | ✅ | archivos
`find` | `dir /s /b` | Buscar archivos | ✅ | archivos
`ps` / `top` / `tasklist` | `tasklist` | Procesos | ✅ | procesos
`df -h` / `df` | `wmic logicaldisk get ...` | Espacio en disco | ✅ | almacenamiento
`free -h` / `free` | `wmic OS get ...` | Memoria RAM | ✅ | memoria
`ping host` | `ping host` | Conectividad | ✅ | red
`ifconfig` / `ipconfig` | `ipconfig /all` | Red | ✅ | red
`netstat` | `netstat -ano` | Conexiones activas | ✅ | red
`curl` | `curl` | Transferir datos | ✅ | red
`echo` | `echo` | Imprimir texto | ✅ | consola
`history` | `doskey /history` | Historial | ✅ | consola
`man` / `help` | `help` | Ayuda | ✅ | consola
`cd ..` / `cd /` / `cd ~` | `cd ..` / `cd \` / `cd %USERPROFILE%` | Navegación | ✅ | navegación
`cp` | `copy` | Copiar | ❌ | archivos
`mv` | `move` | Mover/renombrar | ❌ | archivos
`rm` | `del` | Eliminar archivo | ❌ | archivos
`rm -rf` | `rd /s /q` | Eliminar directorio recursivo | ❌ | archivos
`mkdir` / `md` | `md` | Crear directorio | ❌ | archivos
`rmdir` | `rd` | Eliminar dir vacío | ❌ | archivos
`touch` | `type nul >>` | Crear archivo vacío | ❌ | archivos
`wget` | `curl -L -o` | Descargar archivo | ❌ | red
`apt-get` / `apt` | `winget install` / `winget` | Instalar paquete | ❌ | paquetes
`sudo` | `runas /user:Administrador` | Ejecutar como admin | ❌ | sistema
`exit` / `quit` | `exit` | Salir | ✅ | consola

---

## 5 · Ramificación (branch) de decisión

Cada comando pasa por esta rama antes de ejecutarse:

```
INICIO: operador escribe comando Ubuntu
        │
        ▼
┌─────────────────────┐
│ ¿Comando conocido?  ├─ No ──► "orden no encontrada" (use 'mapa')
└──────────┬──────────┘
           │ Sí
           ▼
┌─────────────────────┐
│ ¿Variante = apt?    ├─ No ──► Rama: standard_solo_lectura
└──────────┬──────────┘
           │ Sí
           ▼
┌─────────────────────┐
│ ¿IP = 192.168.100.20│─ No ──► Rama: IP1 (servidor C2 real)
│  (honeypot)?        ├─ Sí ──► Rama: honeypot_cebo (IP 2)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ¿Comando seguro?    ├─ No ──► Rama: solo_mostrar_servicio (no ejecuta)
└──────────┬──────────┘
           │ Sí
           ▼
    Ejecutar comando Windows equivalente
           │
           ▼
    Registrar log forense (timestamp, IP, usuario, comando, hash SHA-256)
```

En el código (`ubuntu_win_sim.py`), esta rama está en la función `rama_decision()`:

```python
def rama_decision(comando, variante, ip, seguro):
    if comando no conocido:
        return "no_encontrado"
    if variante == "standard":
        return "standard_solo_lectura"
    if ip == "192.168.100.20":
        return "honeypot_cebo"
    if not seguro:
        return "solo_mostrar_servicio"
    return "ejecutar_real"
```

---

## 6 · Proceso de implementación paso a paso

### Día 1 — Base del simulador
1. Crear `ubuntu_win_sim.py` con el índice de comandos, colores ANSI, prompt tipo Ubuntu.
2. Añadir función `mostrar_servicio()` que imprima el "servicio a hacer" antes de ejecutar.
3. Probar comandos seguros (`pwd`, `whoami`, `ls`, `date`, `ps`).

### Día 2 — 2 variantes y ramificación
4. Agregar parámetro `--edition {standard|apt}`.
5. Implementar la rama de decisión (branch): standard vs apt, IP1 vs IP2, seguro vs no seguro.
6. Comandos no seguros (`cp`, `rm`, `mkdir`, `wget`, `apt`) solo muestran el servicio, no ejecutan.

### Día 3 — 2 IPs y 1 servidor
7. Agregar parámetro `--ip {192.168.100.10|192.168.100.20}`.
8. IP 1 → conecta al servidor C2-DECT real (puerto 8443).
9. IP 2 → modo honeypot: simula servicios Ubuntu, no hay servidor real detrás, todo se captura.

### Día 4 — Logs forenses
10. Crear `logs/terminal_sim.log` con formato JSON por línea:
    ```json
    {"ts":"2026-11-17T12:00:00Z","ip":"192.168.100.10","variante":"apt",
     "usuario":"USER1","cmd":"ls -l","win":"dir /q","seguro":true,
     "rama":"standard_solo_lectura","hash":"sha256..."}
    ```
11. Hash SHA-256 de cada entrada para encadenamiento de evidencia.

### Día 5 — Honeypot de terminal (solo variante apt + IP 2)
12. Modo cebo: al detectar comandos ofensivos (`rm -rf`, `wget`, `sudo`, `apt-get`),
    responder como si fueran reales pero solo registrar.
13. Generar alerta cuando un atacante probe el honeypot.

### Día 6 — Integración con C2-DECT
14. Vincular el simulador al servidor `c2-server.exe` (puerto 8443).
15. Probar E2E: operador en terminal simulada → comando indexado → servidor C2 recibe check-in.

---

## 7 · ¿Vale la pena implementar Honeypots de Terminal?

**Respuesta corta: SÍ, vale la pena, pero solo en la variante apt y solo como capa de detección, nunca como única defensa.**

### Ventajas (Pros)
| Punto | Explicación |
|-------|-------------|
| **Detección temprana** | Un honeypot de terminal no tiene usuarios legítimos. Cualquier interacción es sospechosa por definición. |
| **Bajo ruido, alta señal** | A diferencia de un IDS en red, un honeypot de terminal genera pocos falsos positivos: si alguien escribe comandos, está atacando. |
| **Inteligencia de amenazas** | Captura qué comandos intenta el atacante (`rm -rf`, `wget`, `sudo`, `apt-get`), qué variantes prefiere, y su patrón de movimiento. |
| **Retraso al atacante** | El atacante pierde tiempo interactuando con un sistema simulado mientras el equipo azul se alerta. |
| **Evidencia forense** | Cada comando queda registrado con hash; útil para auditoría y cadena de custodia en Red Team autorizado. |

### Riesgos y contras (Cons)
| Punto | Explicación |
|-------|-------------|
| **Falso sentido de seguridad** | Un honeypot no protege sistemas reales. Si confías solo en él, te atacan donde no hay cebo. |
| **Mantenimiento** | Debe seguir pareciendo real (versión de Ubuntu, prompt, respuestas coherentes) o el atacante lo detecta rápido. |
| **Riesgo legal** | Capturar IPs y comandos de terceros puede tener implicaciones legales. Solo usar en laboratorio con alcance declarado. |
| **Riesgo de escape** | Si el honeypot ejecuta comandos reales, podría usarse como trampolín. Por eso en este diseño los comandos no seguros **nunca se ejecutan**, solo se muestra el "servicio a hacer". |

### Recomendación para C2-DECT

Implementar el **Honeypot de Terminal** bajo estas condiciones:

1. **Solo en variante apt** (la edición ofensiva tiene más necesidad de detección y contra-inteligencia).
2. **Solo en IP 2** (192.168.100.20), separada de la IP 1 del servidor C2 real.
3. **Modo solo-lectura / simulación**: el honeypot nunca ejecuta comandos destructivos. Solo muestra el "servicio a hacer" y registra.
4. **Con alcance declarado**: documento de reglas de compromiso firmado antes de exponerlo a red.
5. **Integra con logs forenses**: cada interacción del honeypot genera una entrada con SHA-256 para cadena de custodia.

**Veredicto:** Vale la pena como módulo de detección y engaño dentro de un laboratorio de Red Team autorizado. No reemplaza un firewall, EDR o segmentación de red; los complementa.

---

## 8 · Cómo ejecutar el simulador

```powershell
# Variante standard, IP del servidor C2 (IP 1)
python "linux ubuntu service\ubuntu_win_sim.py" --edition standard --ip 192.168.100.10

# Variante apt, IP del honeypot (IP 2) — modo cebo activo
python "linux ubuntu service\ubuntu_win_sim.py" --edition apt --ip 192.168.100.20 --honeypot

# Dentro del simulador:
#   mapa        -> índice completo de comandos indexados
#   servicios   -> servicios tipo 2 del sistema
#   branch      -> rama de decisión actual
#   clear       -> limpiar pantalla
#   exit        -> salir
```

---

## 9 · Archivos entregables

| Archivo | Propósito |
|---------|-----------|
| `ubuntu_win_sim.py` | Simulador de terminal Ubuntu (2 variantes, 2 IPs, 1 servidor, rama, honeypot, logs) |
| `DISEÑO.md` | Este documento de diseño |
| `logs/terminal_sim.log` | Log forense JSON por línea (generado en runtime) |

---

> **Recordatorio de uso:** Uso exclusivo para testing de seguridad autorizado, operaciones de Red Team y laboratorios de detección con alcance declarado. No operar contra activos de terceros sin autorización escrita vigente.
