# Guion Completo para el Curso de Sistemas Operativos
## Simulador de Servidor Ubuntu: Servicios, Comandos Esenciales y Simulación de Ataque

> Carpeta: `C:\Users\USER1\Desktop\test\cs2\linux ubuntu service\`  
> Archivos usados: `ubuntu_server_sim.py`, `launch_3_ventanas.py`, `mapa_segmentos.py`  
> Nivel: Principiante · Idioma: Español con términos técnicos explicados

---

## Índice

1. [Los servicios del servidor (qué son y para qué sirven)](#1-servicios)
2. [Comandos esenciales de Ubuntu explicados en lenguaje sencillo](#2-comandos)
3. [La simulación: 3 ventanas (Servidor, Atacante, Víctima)](#3-simulacion)
4. [Escenario completo paso a paso](#4-escenario)
5. [Glosario de términos técnicos](#5-glosario)

---

<a name="1-servicios"></a>
## 1 · Los servicios del servidor

### ¿Qué es un servicio?

Un **servicio** (también llamado "demonio" o *daemon*) es un programa que se queda ejecutándose en silencio, esperando peticiones. Piensa en él como un empleado que trabaja las 24 horas sin dormir:

*   El **recepcionista** atiende visitas.
*   El **cartero** entrega paquetes.
*   El **archivista** guarda documentos.

En Ubuntu, cada servicio escucha en una **puerta** llamada **puerto**. Si no hay un servicio escuchando en esa puerta, nadie puede entrar por allí.

### Los 3 servicios que simulamos

| Servicio | Puerto | Analogía sencilla | Para qué sirve en la vida real |
|----------|--------|-------------------|--------------------------------|
| **ssh** | 22 | El guardia de entrada con llave | Permite entrar al servidor de forma remota y segura, como si te conectaras por un cable cifrado desde tu casa. |
| **apache2** | 80 | El recepcionista de una oficina | Sirve páginas web. Cuando visitas una URL, él te entrega el contenido. |
| **smbd** | 445 | El archivista de carpetas compartidas | Permite compartir archivos y carpetas entre computadoras (como cuando en Windows compartes una carpeta en la red). |

### Comandos para manejar servicios

En Ubuntu se usa `systemctl` para decirle al sistema qué hacer con un servicio:

| Comando | Qué significa en lenguaje cotidiano |
|---------|-------------------------------------|
| `systemctl status apache2` | "¿Está prendido el recepcionista Apache?" |
| `systemctl start apache2` | "Enciende el recepcionista Apache" |
| `systemctl stop apache2` | "Apaga el recepcionista Apache" |
| `systemctl restart apache2` | "Apaga y prende otra vez al recepcionista Apache" |
| `service ssh status` | "¿Está prendido el guardia ssh?" (forma antigua de decir lo mismo) |

---

<a name="2-comandos"></a>
## 2 · Comandos esenciales de Ubuntu explicados en lenguaje sencillo

A continuación, los comandos más importantes que todo estudiante de Sistemas Operativos debe conocer. Cada uno incluye su significado y el equivalente en Windows (porque nuestro simulador corre sobre Windows).

### A. Información del sistema

| Comando Ubuntu | Equivalente Windows | Qué hace (en lenguaje sencillo) |
|----------------|---------------------|---------------------------------|
| `hostnamectl` | `systeminfo` | Muestra el nombre de la computadora, el sistema operativo y el hardware. |
| `hostname` | `hostname` | Solo muestra el nombre de la computadora (ej. `pardoserver`). |
| `uname -a` | `systeminfo` | Muestra detalles del "corazón" del sistema (kernel). |
| `date` | `date /t` | Muestra la fecha y hora actuales del servidor. |
| `uptime` | `net statistics workstation` | Cuenta cuánto tiempo lleva el servidor prendido sin reiniciar. |

### B. Red y conexión a internet

| Comando Ubuntu | Equivalente Windows | Qué hace (en lenguaje sencillo) |
|----------------|---------------------|---------------------------------|
| `ip addr` o `ip a` | `ipconfig /all` | Muestra las direcciones IP de la computadora (su "dirección postal" en la red). |
| `hostname -I` | `ipconfig` | Muestra solo las direcciones IP, sin detalles extra. |
| `ifconfig` | `ipconfig /all` | Forma antigua de ver la configuración de red (igual que `ip addr`). |
| `ping` | `ping` | Envía señales a otra computadora para saber si está conectada y responde. |
| `netstat -tulpn` | `netstat -ano` | Muestra qué puertas (puertos) están abiertas y qué programas las están usando. |

### C. Archivos y carpetas

| Comando Ubuntu | Equivalente Windows | Qué hace (en lenguaje sencillo) |
|----------------|---------------------|---------------------------------|
| `pwd` | `cd` | Muestra en qué carpeta te encuentras ahora mismo. |
| `ls` | `dir` | Lista los archivos y carpetas de la carpeta actual. |
| `ls -l` | `dir /q` | Lista archivos con detalles extra (quién es el dueño, tamaño, fecha). |
| `cat archivo` | `type archivo` | Muestra el contenido de un archivo de texto en pantalla. |
| `whoami` | `whoami` | Te dice con qué usuario estás conectado. |

### D. Logs y registros

| Comando Ubuntu | Equivalente Windows | Qué hace (en lenguaje sencillo) |
|----------------|---------------------|---------------------------------|
| `journalctl` | `eventvwr` | Abre el cuaderno donde el sistema anota todo lo que pasa (errores, avisos, inicios de sesión). |
| `dmesg` | `wevtutil` | Muestra mensajes del "corazón" del sistema (kernel) al arrancar. |

### E. Comandos especiales del simulador

| Comando | Qué hace en el simulador |
|---------|--------------------------|
| `mapa` | Muestra la lista completa de comandos Ubuntu y su equivalente en Windows. |
| `servicios` o `status` | Muestra si ssh, apache2 y smbd están prendidos o apagados. |
| `ver logs` | Muestra todas las acciones registradas (quién hizo qué y cuándo). |
| `mapa segmentos` | Abre una ventana separada dibujando el mapa de la red y quién está comprometido. |
| `clear` | Limpia la pantalla (borra lo escrito anteriormente). |
| `exit` o `quit` | Sale del simulador. |

---

<a name="3-simulacion"></a>
## 3 · La simulación: 3 ventanas

Nuestro simulador abre **tres consolas de Windows separadas**. Cada una representa un rol distinto en una red:

| Ventana | Rol | Usuario | Contraseña | IP simulada | ¿Qué puede hacer? |
|---------|-----|---------|------------|-------------|-------------------|
| 1 | **Servidor** | `admin` | `luis` | `192.168.100.10` | Ver todos los logs, manejar servicios, ver el mapa completo. |
| 2 | **Atacante** | `operador1` | `op123` | `192.168.100.21` | Escanear puertos, intentar exploits simulados. |
| 3 | **Víctima** | `operador2` | `op123` | `192.168.100.22` | Ver alertas de ataques recibidos, recibir comandos del servidor. |

### ¿Cómo se comunican?

Todas las acciones se escriben en un **archivo de logs compartido** (`logs/shared_logs.jsonl`). Es como un cuaderno común donde todos anotan lo que hacen. El servidor puede leer todo el cuaderno; los otros solo ven lo suyo.

---

<a name="4-escenario"></a>
## 4 · Escenario completo paso a paso

Sigue este orden para hacer la práctica en clase.

### Paso 0: Abrir las 3 ventanas

Desde una terminal de Windows, ubicada en la carpeta `linux ubuntu service\`, escribe:

```powershell
python launch_3_ventanas.py
```

Se abrirán 3 consolas automáticamente. En cada una, inicia sesión con los datos de la tabla anterior.

---

### Caso A: Revisar los servicios del servidor (Apache)

**Ventana 1 — Servidor (`admin` / `luis`):**

```
admin@pardoserver:~$ servicios
```

Verás algo así:

```
┌─[ SERVICIOS DEL SERVIDOR ]────────────────────────────────────┐
  ssh          │ activo (running) │ puerto 22 │ OpenSSH secure shell server
  apache2      │ activo (running) │ puerto 80 │ Apache HTTP Server
  smbd         │ activo (running) │ puerto 445│ Samba SMB Daemon
└───────────────────────────────────────────────────────────────┘
```

**¿Qué significa?**
- **ssh activo**: puedes entrar al servidor de forma remota.
- **apache2 activo**: el servidor está publicando una página web en el puerto 80.
- **smbd activo**: comparte archivos en la red.

Ahora revisa el detalle de Apache:

```
admin@pardoserver:~$ systemctl status apache2
```

Verás:

```
● apache2.service - The Apache HTTP Server
     Active: active (running)
```

**Significado:** `active (running)` = prendido y funcionando. Si dijera `inactive (dead)`, estaría apagado.

---

### Caso B: Comandos de red esenciales

**Ventana 1 — Servidor:**

```
admin@pardoserver:~$ ip a
```

Verás algo como:

```
   Dirección IPv4. . . . . . . . . . . . : 192.168.100.10
```

Esto es la "dirección postal" del servidor en la red.

**Ventana 2 — Atacante:**

```
operador1@op1-endpoint:~$ ping 192.168.100.10
```

Esto pregunta: "¿Estás ahí, servidor?". Si responde, hay conexión.

**Ventana 1 — Servidor:**

```
admin@pardoserver:~$ hostname -I
192.168.100.10
```

Muestra solo las IP, sin detalles extra.

---

### Caso C: Simular un ataque y ver el mapa de compromiso

**Ventana 2 — Atacante (`operador1` / `op123`):**

```
operador1@op1-endpoint:~$ scan 192.168.100.22
```

Verás:

```
[ATAQUE] Escaneando 192.168.100.22...
  Puerto 22 (ssh):    abierto
  Puerto 80 (http):   abierto
  Puerto 445 (smbd):  abierto
[simulador] Escaneo completado contra 192.168.100.22
```

Ahora el atacante intenta entrar:

```
operador1@op1-endpoint:~$ exploit 192.168.100.22
```

Verás:

```
[ATAQUE] Ejecutando exploit contra 192.168.100.22...
  CVE-2023-XXXX: intento de desbordamiento de búfer en smbd
  Resultado: ACCESO OBTENIDO (simulado)
[simulador] Explotación completada contra 192.168.100.22
```

**¿Qué pasó?** La víctima (`op2-endpoint`) ahora está **comprometida**. El simulador lo anotó en su mapa interno.

---

**Ventana 3 — Víctima (`operador2` / `op123`):**

```
operador2@op2-endpoint:~$ alertas
```

Verás algo como:

```
┌─[ LOG DE ACTIVIDAD ]───────────────────────────────────────────┐
  2026-11-17T18:10:46 operator1(op1-endpoint) 192.168.100.22  ataque   scan 192.168.100.22...
└─────────────────────────────────────────────────────────────────┘
```

La víctima puede ver que alguien la escaneó.

---

**Ventana 1 — Servidor (`admin` / `luis`):**

```
admin@pardoserver:~$ ver logs
```

El servidor ve TODO:

```
┌─[ LOG DE ACTIVIDAD ]───────────────────────────────────────────┐
  2026-11-17T18:10:46 operator1(op1-endpoint) 192.168.100.22  ataque   scan 192.168.100.22...
  2026-11-17T18:10:48 operator1(op1-endpoint) 192.168.100.22  ataque   exploit 192.168.100.22...
└─────────────────────────────────────────────────────────────────┘
```

---

### Caso D: Ver el mapa de segmentos

Desde **cualquiera de las 3 ventanas**, escribe:

```
mapa segmentos
```

Se abrirá una **ventana separada** (la ventana 4) con este aspecto:

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

**Interpretación:**
- El servidor está seguro.
- El atacante está en su rol (amarillo).
- La víctima está comprometida (rojo ☠).
- La conexión del atacante a la víctima fue exitosa (rojo ✗).

---

<a name="5-glosario"></a>
## 5 · Glosario de términos técnicos

| Término | Significado sencillo |
|---------|---------------------|
| **Servicio / Daemon** | Programa que trabaja en segundo plano, esperando peticiones (como un recepcionista siempre despierto). |
| **Puerto** | Una "puerta" numerada por donde entra y sale información (ej. 80 = web, 22 = ssh, 445 = archivos). |
| **IP** | Dirección única de una computadora en la red (su "dirección postal"). |
| **systemctl** | Herramienta de Ubuntu para encender, apagar o revisar servicios. |
| **Active (running)** | El servicio está prendido y funcionando. |
| **Inactive (dead)** | El servicio está apagado. |
| **Log / Bitácora** | Archivo donde el sistema anota todo lo que ocurre (errores, visitas, inicios de sesión). |
| **Comprometido** | Cuando un atacante logró entrar y controlar una computadora. |
| **Escaneo (scan)** | Revisar qué puertas tiene abiertas una computadora para buscar puntos débiles. |
| **Exploit** | Intento de entrar aprovechando un fallo o vulnerabilidad. |
| **Víctima** | La computadora que recibe el ataque. |
| **Atacante** | La computadora que lanza el ataque. |

---

> **Nota final:** Todo esto es una **simulación educativa**. No se instala ni ejecuta software real peligroso. Los comandos de C2-DECT (`c2-server`, `build-*`, etc.) también están disponibles como comandos nativos si se quiere avanzar en la simulación de operaciones de seguridad.
