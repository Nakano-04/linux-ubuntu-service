# -*- coding: utf-8 -*-
"""Genera el documento Word de sustentación del EC3 / Curso de Sistemas Operativos
a partir de los cuatro archivos .md del laboratorio."""

import os
import re

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = r"C:\Users\USER1\Desktop\test\cs2\linux ubuntu service"
OUT = os.path.join(BASE, "DOCUMENTO_SUSTENTACION_CURSO_SO.docx")

MD_FILES = [
    ("PARTE I — DISEÑO DEL SIMULADOR DE TERMINAL UBUNTU SOBRE WINDOWS", "DISEÑO.md"),
    ("PARTE II — DISEÑO DEL SIMULADOR DE SERVIDOR UBUNTU (3 ROLES)", "DISEÑO_SERVER.md"),
    ("PARTE III — GUION COMPLETO PARA EL CURSO DE SISTEMAS OPERATIVOS", "GUION_CURSO_SO.md"),
    ("PARTE IV — GUION: DOS TIPOS DE SERVIDOR WEB (APACHE Y NGINX)", "GUION_DISTRIBUCIONES.md"),
]

AZUL = RGBColor(0x1F, 0x3B, 0x63)
GRIS = RGBColor(0x59, 0x59, 0x59)


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------
def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def shade_paragraph(p, fill):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


INLINE_RE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*)")


def add_rich_to_paragraph(p, text):
    """Convierte `código` y **negrita** del markdown en runs de Word."""
    text = text.replace("\\|", "|").replace("<br>", " ")
    for token in INLINE_RE.split(text):
        if not token:
            continue
        if token.startswith("`") and token.endswith("`") and len(token) > 1:
            run = p.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0xA0, 0x30, 0x30)
        elif token.startswith("**") and token.endswith("**") and len(token) > 3:
            run = p.add_run(token[2:-2])
            run.bold = True
        else:
            p.add_run(token)


def rich_paragraph(doc, text, style=None):
    p = doc.add_paragraph(style=style)
    add_rich_to_paragraph(p, text)
    return p


def code_block(doc, lines):
    for line in lines:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.left_indent = Inches(0.18)
        run = p.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(8)
        shade_paragraph(p, "F2F2F2")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def is_separator(line):
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def add_table(doc, rows):
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j in range(ncols):
            cell = table.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            txt = row[j] if j < len(row) else ""
            add_rich_to_paragraph(p, txt)
            for run in p.runs:
                run.font.size = Pt(9)
            if i == 0:
                shade_cell(cell, "1F3B63")
                for run in p.runs:
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    run.bold = True
            elif i % 2 == 0:
                shade_cell(cell, "F7F9FC")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Universidad Científica del Sur — Sistemas Operativos — EC3  |  Página ")
    r.font.size = Pt(8)
    r.font.color.rgb = GRIS
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    p._p.append(fld)


def add_header(section):
    p = section.header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("UCSUR · Sistemas Operativos · Laboratorio linux ubuntu service")
    r.font.size = Pt(8)
    r.font.color.rgb = GRIS


# ---------------------------------------------------------------------------
# Documento base
# ---------------------------------------------------------------------------
doc = Document()
props = doc.core_properties
props.author = "Luis Roberto Baldeón Sarmiento"
props.last_modified_by = "Luis Roberto Baldeón Sarmiento"
props.title = "Sustentación EC3 — Laboratorio de Servicios basado en Sistema Operativo Linux"
props.subject = "Curso de Sistemas Operativos — Universidad Científica del Sur"
props.keywords = "Sistemas Operativos, Ubuntu, servicios, Apache2, SSH, Samba, logs, EC3"
props.comments = "Documento compilado a partir de los archivos .md del laboratorio linux ubuntu service."
sec = doc.sections[0]
sec.top_margin = Inches(0.85)
sec.bottom_margin = Inches(0.85)
sec.left_margin = Inches(0.85)
sec.right_margin = Inches(0.85)
add_header(sec)
add_footer(sec)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
for lvl, size in ((1, 16), (2, 14), (3, 12), (4, 11)):
    st = doc.styles[f"Heading {lvl}"]
    st.font.name = "Calibri"
    st.font.size = Pt(size)
    st.font.color.rgb = AZUL
    st.font.bold = True

# ----------------------------- Portada -------------------------------------
for _ in range(3):
    doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("UNIVERSIDAD CIENTÍFICA DEL SUR")
r.bold = True
r.font.size = Pt(16)
r.font.color.rgb = AZUL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("EVALUACIÓN CONTINUA 3 (EC3)")
r.bold = True
r.font.size = Pt(13)
r.font.color.rgb = GRIS

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("DOCUMENTO DE SUSTENTACIÓN DEL LABORATORIO")
r.bold = True
r.font.size = Pt(20)
r.font.color.rgb = AZUL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Servicios basados en Sistema Operativo Linux")
r.font.size = Pt(14)
r.font.color.rgb = AZUL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Simulador de terminal Ubuntu, simulador de servidor de 3 roles,\n"
              "guiones didácticos y evidencia del trabajo desarrollado")
r.italic = True
r.font.size = Pt(11)
r.font.color.rgb = GRIS

doc.add_paragraph()
info = [
    ("Universidad", "Universidad Científica del Sur"),
    ("Curso", "Sistemas Operativos"),
    ("Evaluación", "Evaluación Continua 3 (EC3)"),
    ("Alumno", "Luis Roberto Baldeón Sarmiento"),
    ("Fecha de entrega", "25 de noviembre de 2026"),
    ("Tema del laboratorio", "Servicios basados en Sistema Operativo Linux"),
    ("Ubicación del laboratorio", r"C:\Users\USER1\Desktop\test\cs2\linux ubuntu service"),
    ("Repositorio (privado)", "https://github.com/Nakano-04/linux-ubuntu-service"),
    ("Fuentes compiladas", "DISEÑO.md · DISEÑO_SERVER.md · GUION_CURSO_SO.md · GUION_DISTRIBUCIONES.md"),
]
t = doc.add_table(rows=len(info), cols=2)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (k, v) in enumerate(info):
    c0, c1 = t.cell(i, 0), t.cell(i, 1)
    c0.text = ""
    c1.text = ""
    rp = c0.paragraphs[0]
    rr = rp.add_run(k)
    rr.bold = True
    rr.font.size = Pt(10)
    shade_cell(c0, "DCE6F1")
    rp2 = c1.paragraphs[0]
    rr2 = rp2.add_run(v)
    rr2.font.size = Pt(10)

doc.add_page_break()

# ----------------------------- Resumen -------------------------------------
doc.add_heading("Resumen ejecutivo", level=1)
rich_paragraph(doc, "Este documento compila y ordena todo el trabajo desarrollado por "
              "**Luis Roberto Baldeón Sarmiento**, alumno de la **Universidad Científica del Sur**, "
              "para la **Evaluación Continua 3 (EC3)** del curso de **Sistemas Operativos**. "
              "El laboratorio consiste en un **simulador educativo de Ubuntu 22.04 LTS que se "
              "ejecuta sobre Windows**, pensado para enseñar, sin riesgo real, cómo funcionan "
              "los servicios, los comandos, la red, los registros (logs) y un escenario de "
              "ataque/defensa. El documento sirve de sustentación teórica y técnica de los "
              "archivos entregados y de la demostración en vivo que se realiza desde la terminal.")
for bullet in [
    "Dos diseños complementarios: (1) una terminal Ubuntu indexada a Windows con dos variantes "
    "(standard y apt), dos IPs y un honeypot; (2) un servidor Ubuntu simulado en tres consolas "
    "independientes: Servidor, Atacante y Víctima.",
    "Tres servicios centrales del laboratorio: **ssh (puerto 22)**, **apache2 (puerto 80)** y "
    "**smbd (puerto 445)**, gestionados con systemctl/service.",
    "Un mapa de comandos Ubuntu → Windows que muestra siempre el “servicio a hacer” antes de "
    "ejecutar la acción equivalente.",
    "Logs forenses en formato JSON por línea con timestamp, IP, usuario, rama de decisión y hash "
    "SHA-256; y un log compartido (shared_logs.jsonl) con visibilidad por rol.",
    "Mapa de segmentos de red en una ventana separada que muestra el estado de compromiso de "
    "cada nodo (SEGURO / ATACANTE / COMPROMETIDO).",
    "Cuatro guiones de clase: servicios y comandos esenciales, escenario de ataque, comparativa "
    "Apache vs Nginx y glosario de términos técnicos.",
    "Scripts de apoyo: ubuntu_win_sim.py, ubuntu_server_sim.py, launch_3_ventanas.py, "
    "mapa_segmentos.py, pagina_web_simuladores.html, logs/*.jsonl y configurar_apache2.sh.",
    "Todo el material es una **simulación segura**: los comandos destructivos nunca se ejecutan, "
    "solo se muestra qué haría el sistema operativo real.",
]:
    rich_paragraph(doc, bullet, style="List Bullet")

doc.add_heading("Índice del documento", level=1)
indice = [
    "1. Resumen ejecutivo",
    "2. Marco teórico aplicado al laboratorio",
    "3. Secuencia didáctica y tiempos de ejecución",
    "4. Matriz de cobertura de contenidos del curso",
    "5. Preguntas de control y respuestas",
    "6. Parte I — Diseño del simulador de terminal Ubuntu sobre Windows",
    "7. Parte II — Diseño del simulador de servidor Ubuntu (3 roles)",
    "8. Parte III — Guion completo para el curso de sistemas operativos",
    "9. Parte IV — Guion: dos tipos de servidor web (Apache y Nginx)",
    "10. Anexo A — Inventario de archivos desarrollados",
    "11. Anexo B — Ejecución rápida y análisis del script configurar_apache2.sh",
    "12. Anexo C — Conclusiones para la sustentación",
    "13. Anexo D — Guion en inglés para el video de 6–10 minutos",
    "14. Anexo E — Rúbrica sugerida de evaluación",
    "15. Anexo F — Referencias y comandos de consulta",
]
for item in indice:
    doc.add_paragraph(item, style="List Number")

doc.add_page_break()

# ---------------------------------------------------------------------------
# 2. Marco teórico ampliado
# ---------------------------------------------------------------------------
doc.add_heading("2. Marco teórico aplicado al laboratorio", level=1)
rich_paragraph(doc, "Esta secuencia conecta los contenidos del curso de Sistemas Operativos con "
              "lo que el estudiante ve y ejecuta en el laboratorio. Cada concepto se presenta "
              "con su definición sencilla, su equivalente en el simulador y la evidencia que "
              "puede mostrarse en la sustentación.")

doc.add_heading("2.1 El sistema operativo como capa de abstracción", level=2)
rich_paragraph(doc, "Un **sistema operativo (SO)** es el software que gestiona los recursos de "
              "la computadora y ofrece una interfaz cómoda entre el usuario, las aplicaciones "
              "y el hardware. No se ve directamente, pero se manifiesta cada vez que se abre "
              "un programa, se crea un archivo, se envía un ping o se inicia un servicio. "
              "En este laboratorio el SO simulado es **Ubuntu 22.04 LTS** y se observa desde "
              "una terminal tipo shell con prompt `usuario@equipo:~$`.")
add_table(doc, [
    ("Función del SO", "Manifestación en el laboratorio", "Evidencia / comando"),
    ("Gestión de procesos", "Servicios en segundo plano (ssh, apache2, smbd) y tres consolas independientes", "`systemctl status`, `ps`, `launch_3_ventanas.py`"),
    ("Gestión de memoria", "Cada consola es un proceso con su propio espacio de direcciones", "`tasklist`, Administrador de tareas de Windows"),
    ("Sistema de archivos", "Jerarquía Ubuntu: `/etc`, `/var/log`, `/var/www/html`", "`pwd`, `ls`, `cat`, `configurar_apache2.sh`"),
    ("Entrada/salida y dispositivos", "Terminal, red, archivos de log y página web servida", "`ss -tulpn`, `journalctl`, `ver logs`"),
    ("Protección y seguridad", "Login por rol, usuario root/sudo y reglas de firewall", "`admin/luis`, `operador1/op123`, `sudo ufw allow 80/tcp`"),
    ("Interfaz de usuario", "Shell simulada que interpreta comandos Ubuntu y muestra el equivalente Windows", "`mapa`, `servicios`, prompt `admin@pardoserver:~$`"),
])

doc.add_heading("2.2 Procesos, demonios y systemd", level=2)
rich_paragraph(doc, "Un **proceso** es un programa en ejecución. Cada proceso tiene un identificador "
              "(**PID**), un bloque de control (**PCB**) con su estado, registros, contador de "
              "programa y espacio de memoria. Un proceso pasa por estados **nuevo → listo → "
              "ejecutando → esperando → terminado**; el planificador del kernel decide cuándo "
              "usa la CPU (context switch).")
rich_paragraph(doc, "Un **demonio** o **servicio** es un proceso que permanece en segundo plano, sin "
              "interfaz de usuario, esperando peticiones. En Ubuntu moderno, **systemd** (PID 1) "
              "los administra mediante unidades `.service`. Por eso `systemctl status apache2` "
              "pregunta al gestor de servicios si el proceso Apache sigue vivo y responde con "
              "`active (running)` o `inactive (dead)`.")
code_block(doc, [
    "Estados simples de un proceso:",
    "  NUEVO -> LISTO -> EJECUTANDO -> ESPERANDO -> TERMINADO",
    "",
    "En el laboratorio:",
    "  systemd (PID 1) ---> apache2.service ---> proceso en escucha en el puerto 80",
    "                  ---> ssh.service      ---> proceso en escucha en el puerto 22",
    "                  ---> smbd.service     ---> proceso en escucha en el puerto 445",
])
add_table(doc, [
    ("Concepto", "Definición sencilla", "Ejemplo en el laboratorio"),
    ("Proceso", "Programa en ejecución con PID y PCB", "Cada una de las 3 consolas de Windows"),
    ("Demonio / servicio", "Proceso en segundo plano que espera peticiones", "ssh, apache2, smbd"),
    ("systemd", "Gestor de servicios e init del sistema (PID 1)", "`systemctl status apache2`"),
    ("Unidad .service", "Archivo que describe cómo arrancar un servicio", "`apache2.service`"),
    ("start vs enable", "start enciende ahora; enable lo enciende en cada arranque", "`systemctl enable apache2` en el script .sh"),
    ("active (running)", "El proceso está vivo y atendiendo peticiones", "Salida de `systemctl status apache2`"),
])

doc.add_heading("2.3 Concurrencia y comunicación entre procesos", level=2)
rich_paragraph(doc, "Las tres ventanas del laboratorio son **tres procesos concurrentes**. No comparten "
              "memoria directamente, pero se comunican mediante un archivo: `logs/shared_logs.jsonl`. "
              "Este patrón es una forma sencilla de **comunicación entre procesos (IPC)** mediante "
              "un archivo: cada proceso escribe líneas y el servidor las lee todas.")
rich_paragraph(doc, "El formato **JSON por línea (JSONL)** permite agregar eventos sin reescribir todo "
              "el archivo. Cada línea lleva timestamp, origen, destino, tipo, contenido y un hash "
              "SHA-256 truncado. Como no se implementan bloqueos (locks), en un sistema real podrían "
              "ocurrir condiciones de carrera; por eso se usan marcas de tiempo y hash para ordenar "
              "y verificar la evidencia. Esta limitación se comenta en clase como ejemplo de por qué "
              "los SO ofrecen mecanismos de sincronización.")

doc.add_heading("2.4 Sistema de archivos, rutas y permisos", level=2)
rich_paragraph(doc, "El sistema de archivos organiza la información en un árbol de directorios. En Ubuntu "
              "la raíz es `/`; de ella cuelgan `/etc` (configuración), `/var/log` (registros), "
              "`/var/www/html` (página web de Apache) y `/home` (usuarios). La ruta puede ser "
              "**absoluta** (`/var/www/html/index.html`) o **relativa** (`logs/shared_logs.jsonl`).")
rich_paragraph(doc, "Los permisos y la separación de usuarios son parte de la protección del SO. El rol "
              "`admin` puede ver todos los logs; `operador1` y `operador2` solo lo suyo. Las acciones "
              "administrativas usan `sudo`, equivalente a `runas /user:Administrador` en Windows.")
add_table(doc, [
    ("Ubuntu", "Windows", "Uso en el laboratorio"),
    ("`pwd`", "`cd`", "Saber dónde estamos"),
    ("`ls` / `ls -l`", "`dir` / `dir /q`", "Listar scripts y logs"),
    ("`cat archivo`", "`type archivo`", "Leer index.html o un log"),
    ("`cp`, `mv`, `rm`", "`copy`, `move`, `del`", "Se muestran, no se ejecutan (no seguros)"),
    ("`mkdir`, `touch`", "`md`, `type nul >>`", "Crear directorios/archivos (solo demostración)"),
    ("`tee`", "`more` / redirección", "Escribir la página de prueba desde el .sh"),
])

doc.add_heading("2.5 Redes: direcciones IP, puertos y sockets", level=2)
rich_paragraph(doc, "Una **IP** es la dirección lógica de una máquina en la red; un **puerto** es una "
              "puerta numerada dentro de esa máquina; y un **socket** es la combinación IP + puerto "
              "por la que un servicio escucha. El protocolo ICMP se usa en `ping`, TCP en SSH, HTTP "
              "y SMB. El comando `netstat -tulpn` / `ss -tulpn` responde: ¿qué puertos están abiertos "
              "y qué proceso los usa?")
add_table(doc, [
    ("Servicio", "Puerto", "Protocolo", "Analogía y función real"),
    ("ssh", "22", "TCP", "Guardia con llave: acceso remoto cifrado"),
    ("apache2", "80", "TCP/HTTP", "Recepcionista: entrega páginas web"),
    ("smbd", "445", "TCP/SMB", "Archivista: comparte archivos tipo Windows"),
])

doc.add_heading("2.6 Logs, auditoría e integridad", level=2)
rich_paragraph(doc, "Un **log** es un registro cronológico de eventos. El laboratorio usa dos fuentes: "
              "`journalctl` / `systemd` para los servicios y `shared_logs.jsonl` para las acciones de "
              "los roles. Cada entrada responde a qué, quién, cuándo, desde dónde, hacia dónde y con "
              "qué resultado. El hash SHA-256 permite detectar modificaciones y sostiene la idea de "
              "**cadena de custodia** en un ejercicio de Red Team autorizado.")
add_table(doc, [
    ("Campo del log", "Significado"),
    ("`ts`", "Marca de tiempo UTC del evento"),
    ("`origen_rol`, `origen_host`, `origen_ip`", "Quién generó el evento"),
    ("`destino`", "Objetivo: IP, servicio o sistema"),
    ("`tipo`", "comando, ataque, alerta, reconocimiento o sistema"),
    ("`contenido`", "Descripción legible de la acción"),
    ("`hash`", "SHA-256 truncado para integridad"),
])

doc.add_heading("2.7 Seguridad: AAA, menor privilegio y honeypot", level=2)
rich_paragraph(doc, "El laboratorio practica **AAA**: autenticación (login con usuario y contraseña), "
              "autorización (permisos por rol: el servidor ve todo, los operadores solo lo suyo) y "
              "auditoría (logs con hash). Aplica también el **principio de menor privilegio**: las "
              "acciones destructivas no se ejecutan, solo se muestra el 'servicio a hacer'. El "
              "**honeypot** de la IP 2 (192.168.100.20) simula un Ubuntu real para atraer y registrar "
              "comandos ofensivos sin exponer un sistema verdadero. Finalmente, UFW y la segmentación "
              "de red completan la defensa en profundidad. Todo se hace con alcance declarado y "
              "fines educativos.")

# ---------------------------------------------------------------------------
# 3. Secuencia didáctica
# ---------------------------------------------------------------------------
doc.add_heading("3. Secuencia didáctica y tiempos de ejecución", level=1)
rich_paragraph(doc, "La clase se organiza en sesiones cortas. El estudiante ve primero el concepto, "
              "luego lo ejecuta y finalmente interpreta la salida. La evaluación EC3 exige además "
              "una exposición oral de 1.5–3 minutos en otro idioma y un video de 6–10 minutos con "
              "el rostro visible, explicando una configuración y mostrando el trabajo desde el laboratorio.")
add_table(doc, [
    ("Sesión", "Duración", "Objetivo", "Comandos clave", "Resultado esperado"),
    ("1. Introducción", "15–20 min", "Explicar SO, servicios y demonios", "`servicios`, `systemctl status`", "Los 3 servicios activos con sus puertos"),
    ("2. Comandos esenciales", "25–30 min", "Relacionar Ubuntu con Windows", "`mapa`, `ip a`, `hostname -I`, `pwd`, `ls`", "Tabla de equivalencias comprendida"),
    ("3. Servidor web", "25–30 min", "Configurar/verificar Apache y comparar Nginx", "`systemctl status apache2`, `cat /var/www/html/index.html`", "`active (running)` y página servida"),
    ("4. Ataque y defensa", "25–30 min", "Simular reconocimiento y compromiso", "`scan`, `exploit`, `alertas`", "Víctima comprometida y alerta generada"),
    ("5. Auditoría", "20 min", "Centralizar evidencia y estado de red", "`ver logs`, `mapa segmentos`", "Logs completos y mapa con nodo en rojo"),
    ("6. Sustentación EC3", "1.5–3 min + 6–10 min", "Exponer en inglés y entregar video en línea", "Demo en vivo desde terminal", "Exposición oral + video con rostro visible"),
])

# ---------------------------------------------------------------------------
# 4. Matriz de cobertura
# ---------------------------------------------------------------------------
doc.add_heading("4. Matriz de cobertura de contenidos del curso", level=1)
add_table(doc, [
    ("Contenido del curso", "Tratamiento en el laboratorio", "Evidencia mostrable"),
    ("Arquitectura y abstracción del SO", "Terminal Ubuntu sobre Windows con 'servicio a hacer' antes de ejecutar", "Salida del simulador y tabla Ubuntu→Windows"),
    ("Procesos y planificación", "Demonios gestionados por systemd y rama de decisión por comando", "`systemctl status`, función `rama_decision()`"),
    ("Concurrencia", "Tres consolas escribiendo en un log compartido", "`logs/shared_logs.jsonl`"),
    ("Gestión de memoria", "Procesos separados con espacio propio", "`tasklist` y ventana 4 del mapa"),
    ("Sistema de archivos", "Jerarquía, rutas y creación de index.html", "`pwd`, `cat`, `configurar_apache2.sh`"),
    ("Redes", "IP simuladas, puertos 22/80/445, ping y escaneo", "`ip a`, `netstat -tulpn`, `scan`"),
    ("Seguridad y auditoría", "AAA, honeypot, UFW, logs con hash", "Logins por rol, `ver logs`, `mapa segmentos`"),
    ("Interfaz de usuario", "Shell con prompt usuario@host y comandos nativos", "`admin@pardoserver:~$`"),
])

# ---------------------------------------------------------------------------
# 5. Preguntas de control
# ---------------------------------------------------------------------------
doc.add_heading("5. Preguntas de control y respuestas", level=1)
preguntas = [
    ("¿Qué es un demonio o servicio?", "Un proceso en segundo plano que espera peticiones. En el laboratorio: ssh, apache2 y smbd."),
    ("¿Qué significa `active (running)`?", "Que el servicio está encendido y atendiendo peticiones; lo contrario es `inactive (dead)`."),
    ("¿Cuál es la diferencia entre `start` y `enable`?", "`start` enciende el servicio en la sesión actual; `enable` lo configura para arrancar en cada reinicio."),
    ("¿Por qué Apache escucha en el puerto 80?", "Es el puerto estándar del protocolo HTTP; por eso la página web se sirve en `http://192.168.100.10`."),
    ("¿Cómo se comunican las tres ventanas?", "Mediante el archivo compartido `logs/shared_logs.jsonl`: cada proceso escribe eventos y el servidor los lee todos."),
    ("¿Qué hace `scan` y qué hace `exploit`?", "`scan` busca puertos abiertos (reconocimiento); `exploit` simula aprovechar una vulnerabilidad y marca la víctima como comprometida."),
    ("¿Por qué no se ejecutan los comandos destructivos?", "Porque es una simulación educativa: solo se muestra el equivalente Windows ('servicio a hacer') y se registra en el log."),
    ("¿Qué datos contiene una línea de `shared_logs.jsonl`?", "Timestamp, rol/host/IP de origen, destino, tipo, contenido y hash SHA-256."),
    ("¿Apache o Nginx para muchas visitas simultáneas?", "Nginx es más ligero y eficiente con alta concurrencia; Apache es más fácil de configurar y es el que tiene este laboratorio."),
    ("¿Qué es un honeypot de terminal?", "Un sistema cebo (IP 2) que simula ser real para registrar comandos del atacante sin ejecutar nada peligroso."),
]
for q, a in preguntas:
    rich_paragraph(doc, "**Pregunta:** " + q, style="List Number")
    rich_paragraph(doc, "**Respuesta:** " + a, style="List Bullet")

doc.add_page_break()

# ---------------------------------------------------------------------------
# Convertidor de Markdown a Word
# ---------------------------------------------------------------------------
def convert_markdown(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        # Saltar anclas HTML y reglas horizontales
        if not line or line.startswith("<a name=") or re.fullmatch(r"-{3,}", line):
            i += 1
            continue

        # Bloques de código
        if line.startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i].rstrip())
                i += 1
            i += 1  # cierre
            code_block(doc, block)
            continue

        # Tablas markdown
        if line.startswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            rows = [split_row(line)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            add_table(doc, rows)
            continue

        # Encabezados (desplazados un nivel respecto al título de la parte)
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = min(len(m.group(1)) + 1, 4)
            doc.add_heading(m.group(2).strip(), level=level)
            i += 1
            continue

        # Citas / notas
        if line.startswith(">"):
            p = rich_paragraph(doc, line.lstrip("> ").strip())
            p.paragraph_format.left_indent = Inches(0.25)
            for run in p.runs:
                run.italic = True
                run.font.color.rgb = GRIS
            shade_paragraph(p, "FFF8E1")
            i += 1
            continue

        # Listas
        if re.match(r"^[-*]\s+", line):
            rich_paragraph(doc, re.sub(r"^[-*]\s+", "", line), style="List Bullet")
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line):
            rich_paragraph(doc, re.sub(r"^\d+\.\s+", "", line), style="List Number")
            i += 1
            continue

        # Párrafo normal
        rich_paragraph(doc, line)
        i += 1


for part_title, filename in MD_FILES:
    path = os.path.join(BASE, filename)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()
    doc.add_page_break()
    doc.add_heading(part_title, level=1)
    p = doc.add_paragraph()
    r = p.add_run(f"Contenido íntegro del archivo {filename}, adaptado a este documento.")
    r.italic = True
    r.font.color.rgb = GRIS
    convert_markdown(content)

# ---------------------------------------------------------------------------
# Anexos
# ---------------------------------------------------------------------------
doc.add_page_break()
doc.add_heading("Anexo A — Inventario de archivos desarrollados", level=1)
inventario = [
    ("Archivo", "Tipo", "Función dentro del laboratorio"),
    ("ubuntu_win_sim.py", "Python", "Simulador de terminal Ubuntu indexada a Windows: 2 variantes, 2 IPs, rama de decisión, honeypot y logs forenses."),
    ("ubuntu_server_sim.py", "Python", "Simulador de servidor con 3 roles (Servidor, Atacante, Víctima), logs compartidos y comandos C2-DECT nativos."),
    ("launch_3_ventanas.py", "Python", "Lanzador que abre las 3 consolas de Windows en processes independientes."),
    ("mapa_segmentos.py", "Python", "Ventana separada con el mapa de segmentos y el estado de compromiso de la red."),
    ("pagina_web_simuladores.html", "HTML", "Página web de prueba que el servicio apache2 simulado sirve en el puerto 80."),
    ("configurar_apache2.sh", "Shell script", "Automatiza la instalación, habilitación, configuración y verificación de Apache2 en Ubuntu."),
    ("logs/shared_logs.jsonl", "JSONL", "Log de auditoría compartido: timestamp, origen, destino, tipo, contenido y hash."),
    ("logs/estado_red.json", "JSON", "Estado de compromiso de los segmentos de red (generado en tiempo de ejecución)."),
    ("logs/terminal_sim.log", "JSONL", "Log forense de comandos de la terminal simulada (generado en tiempo de ejecución)."),
    ("DISEÑO.md", "Markdown", "Diseño del simulador de terminal: topología, variantes, índice de comandos y honeypot."),
    ("DISEÑO_SERVER.md", "Markdown", "Diseño del simulador de servidor: roles, ataques, logs y mapa de segmentos."),
    ("GUION_CURSO_SO.md", "Markdown", "Guion didáctico completo para el curso de Sistemas Operativos."),
    ("GUION_DISTRIBUCIONES.md", "Markdown", "Guion de comparativa Apache vs Nginx y escenarios de clase."),
]
add_table(doc, inventario)

doc.add_heading("Anexo B — Ejecución rápida del laboratorio", level=1)
code_block(doc, [
    r"# 1) Abrir las 3 consolas (Servidor, Atacante, Víctima)",
    r"cd C:\Users\USER1\Desktop\test\cs2\linux ubuntu service",
    r"python launch_3_ventanas.py",
    "",
    r"# 2) Logins por defecto",
    r"# Servidor  -> admin / luis      (pardoserver, 192.168.100.10)",
    r"# Atacante  -> operador1 / op123 (op1-endpoint, 192.168.100.21)",
    r"# Víctima   -> operador2 / op123 (op2-endpoint, 192.168.100.22)",
    "",
    r"# 3) Comandos clave en la ventana del Servidor",
    r"servicios",
    r"systemctl status apache2",
    r"ip a",
    r"ver logs",
    r"mapa segmentos",
    "",
    "# 4) Desde el Atacante",
    "scan 192.168.100.22",
    "exploit 192.168.100.22",
    "",
    "# 5) Desde la Víctima",
    "alertas",
    "",
    "# 6) Variante de terminal (opcional)",
    'python ubuntu_win_sim.py --edition standard --ip 192.168.100.10',
    'python ubuntu_win_sim.py --edition apt --ip 192.168.100.20 --honeypot',
    "",
    "# 7) Configuración real de Apache2 en Ubuntu / VM",
    "sudo bash configurar_apache2.sh",
])

doc.add_heading("Análisis línea por línea de configurar_apache2.sh", level=2)
rich_paragraph(doc, "El script entregado automatiza la configuración del servicio Apache2. "
              "Su lectura en voz alta durante la demostración permite justificar cada decisión "
              "técnica ante el docente.")
add_table(doc, [
    ("Bloque del script", "Comandos", "Qué hace y por qué"),
    ("Encabezado y seguridad", "`#!/usr/bin/env bash`, `set -euo pipefail`", "Define el intérprete y detiene el script si hay error, variable sin definir o fallo en tubería."),
    ("Variables", "`SERVICE=apache2`, `PORT=80`, `INDEX_FILE=/var/www/html/index.html`", "Centraliza los valores para no repetirlos y facilitar cambios."),
    ("Paso 1", "`sudo apt-get update -y`", "Actualiza el índice de paquetes para instalar una versión disponible."),
    ("Paso 2", "`sudo apt-get install -y apache2`", "Instala el demonio Apache2; equivale a habilitar el servicio web del laboratorio."),
    ("Paso 3", "`systemctl enable` + `systemctl restart`", "Arranca el servicio ahora y lo deja configurado para el próximo arranque."),
    ("Paso 4", "`ufw status` / `ufw allow 80/tcp`", "Abre el puerto HTTP solo si el firewall está activo; aplica menor privilegio."),
    ("Paso 5", "`sudo tee ... <<'HTML'`", "Crea una página de prueba en la raíz documental de Apache para poder verificar con curl."),
    ("Paso 6", "`systemctl status`, `ss -tulpn`, `curl`, `journalctl`", "Verifica proceso, puerto escuchando, respuesta HTTP y registros del servicio."),
    ("Cierre", "`echo DONE ...`", "Confirma visualmente que la configuración terminó con éxito."),
])

doc.add_heading("Anexo C — Conclusiones para la sustentación", level=1)
for txt in [
    "El laboratorio permite **ver conceptos abstractos del curso de Sistemas Operativos en "
    "acción**: los servicios son procesos en segundo plano (demonios) que esperan peticiones "
    "en un puerto; el usuario interactúa con ellos mediante comandos y el sistema registra "
    "cada evento en logs.",
    "La gestión de procesos se practica con `systemctl status|start|stop|restart` y con "
    "`ps`/`top` (equivalente Windows: `tasklist`). Las tres consolas son **tres procesos "
    "independientes** que se comunican mediante un archivo compartido.",
    "La gestión de E/S y de archivos se trabaja con `pwd`, `ls`, `cat`, `cp`, `mv`, `rm` y con "
    "la creación de `/var/www/html/index.html` desde el script `configurar_apache2.sh`.",
    "La red se enseña con `ip addr`, `hostname -I`, `ping` y `netstat -tulpn`, identificando "
    "las “puertas” 22 (ssh), 80 (Apache) y 445 (Samba).",
    "La seguridad se aborda desde una simulación: escaneo, exploit simulado, alertas en la "
    "víctima, auditoría central en el servidor y mapa de compromiso; sin ejecutar código "
    "destructivo real.",
    "El diseño de ramificación (`rama_decision`) muestra cómo un sistema toma decisiones según "
    "el tipo de comando, la variante y la IP, reforzando el análisis de algoritmos y estados.",
    "Como Material de sustentación, el documento y los scripts permiten explicar en inglés, "
    "en 1.5–3 min, el tema central y en 6–10 min la configuración de Apache2, mostrando "
    "todo directamente desde la terminal del laboratorio.",
]:
    rich_paragraph(doc, txt, style="List Bullet")

p = doc.add_paragraph()
r = p.add_run("Nota de uso: este laboratorio se emplea exclusivamente para fines educativos y "
              "testing autorizado. No se operan activos de terceros sin autorización escrita.")
r.italic = True
r.font.color.rgb = GRIS

# ---------------------------------------------------------------------------
# Anexo D — Guion en inglés para el video
# ---------------------------------------------------------------------------
doc.add_page_break()
doc.add_heading("Anexo D — Guion en inglés para el video de 6–10 minutos", level=1)
rich_paragraph(doc, "El siguiente guion cumple la consigna de exponer en otro idioma. Está previsto "
              "para un video de aproximadamente 8 minutos, con la cámara encendida y compartiendo "
              "pantalla sobre el laboratorio. La exposición oral corta de 1.5–3 minutos puede ser "
              "el resumen de los primeros dos bloques.")

doc.add_heading("D.1 Versión corta (1.5–3 minutos, oral)", level=2)
code_block(doc, [
    "Good morning. My name is Luis Roberto Baldeon Sarmiento, from Universidad",
    "Cientifica del Sur. Today I will present my EC3 laboratory for the Operating",
    "Systems course.",
    "",
    "The topic is a Linux services lab: an Ubuntu 22.04 simulator that runs on",
    "Windows. It teaches services, processes, commands, logs and a simulated attack.",
    "The three main services are SSH on port 22, Apache2 on port 80 and Samba on",
    "port 445. They are daemons, background processes managed by systemd.",
    "",
    "For this presentation I will focus on one configuration: Apache2.",
    "I will show systemctl status apache2, the 'active (running)' state, port 80",
    "listening, the test page and the journal logs. Everything is shown directly",
    "from the terminal, and the destructive commands are never executed.",
    "",
    "This is a safe simulation for the classroom. Thank you.",
])

doc.add_heading("D.2 Versión larga (6–10 minutos, video con rostro visible)", level=2)
add_table(doc, [
    ("Tiempo", "Qué se muestra en pantalla", "Qué se dice (en inglés)"),
    ("0:00–0:40", "Rostro en cámara, luego portada del repo", "\"Hi, I am Luis Roberto Baldeon Sarmiento. This is my EC3 deliverable for the Operating Systems course at Universidad Cientifica del Sur. The topic is a Linux services laboratory.\""),
    ("0:40–1:40", "Carpeta del laboratorio y `ls -l`", "\"Here are the developed files: two simulators, a three-window launcher, a segment map, an HTML page, logs and an Apache configuration script.\""),
    ("1:40–2:40", "Diagrama de los 3 roles", "\"The lab opens three independent Windows processes: the server, the attacker and the victim. They communicate through a shared JSON Lines log file.\""),
    ("2:40–3:40", "`servicios` y tabla ssh/apache2/smbd", "\"These are the three daemons. A daemon is a process that runs in the background and waits for requests on a port. SSH uses port 22, Apache uses port 80 and Samba uses port 445.\""),
    ("3:40–5:40", "`systemctl status apache2`, `ss -tulpn`, `curl`", "\"Now the configuration I will explain is Apache2. I install it, enable it at boot, restart it, and verify that the service is active and that port 80 is listening. The curl response confirms the page is served.\""),
    ("5:40–6:50", "`configurar_apache2.sh` con `cat`", "\"This script automates all those steps: update, install, enable, open the firewall, deploy the test page and verify with journalctl.\""),
    ("6:50–8:00", "`scan`, `alertas`, `ver logs`, `mapa segmentos`", "\"For the security part, the attacker scans the victim, the victim sees the alert, and the server audits everything. The segment map shows the compromised node in red.\""),
    ("8:00–8:40", "Rostro en cámara y cierre", "\"In summary, the lab makes abstract Operating Systems concepts visible: processes, services, files, networks, logs and security. All commands are simulated, so it is safe for class. Thank you for watching.\""),
])

# ---------------------------------------------------------------------------
# Anexo E — Rúbrica sugerida
# ---------------------------------------------------------------------------
doc.add_heading("Anexo E — Rúbrica sugerida de evaluación", level=1)
add_table(doc, [
    ("Criterio", "Nivel alto (lo esperado)", "Evidencia en el laboratorio"),
    ("Dominio del tema", "Define servicio, demonio, puerto, proceso y log con lenguaje propio", "Explicación durante la demo y respuestas del Anexo 5"),
    ("Configuración elegida", "Ejecuta y justifica Apache2 paso a paso", "`systemctl`, `ss`, `curl`, `journalctl`, script .sh"),
    ("Demostración en vivo", "Trabaja desde la terminal, sin PDF ni solo modo gráfico", "Consolas abiertas y comandos ejecutados en pantalla"),
    ("Expresión en otro idioma", "Exposición clara de 1.5–3 min y video en inglés", "Guion del Anexo D"),
    ("Video", "6–10 min, realizado en línea y con el rostro visible", "Archivo de video entregado"),
    ("Análisis y seguridad", "Interpreta logs, alertas y mapa de compromiso; menciona que es simulación", "`ver logs`, `alertas`, `mapa segmentos`"),
    ("Puntualidad y orden", "Entrega dentro de la fecha y con archivos organizados", "Repo privado y artefactos listos"),
])

# ---------------------------------------------------------------------------
# Anexo F — Referencias
# ---------------------------------------------------------------------------
doc.add_heading("Anexo F — Referencias y comandos de consulta", level=1)
for txt in [
    "`man systemctl`, `man service`, `man journalctl`, `man ss`, `man netstat`, `man apache2` — páginas de manual de Ubuntu.",
    "Ubuntu Server Guide — administración de servicios, redes y firewall UFW.",
    "Documentación oficial de Apache HTTP Server — configuración del servicio y raíz documental `/var/www/html`.",
    "Documentación oficial de Nginx — comparativa con Apache y comando `nginx -t`.",
    "RFC 9110 (HTTP), RFC 4251 (SSH) y especificación SMB — base de los puertos 80, 22 y 445.",
    "Material interno del curso de Sistemas Operativos de la Universidad Científica del Sur: procesos, memoria, archivos, E/S y redes.",
]:
    rich_paragraph(doc, txt, style="List Bullet")

doc.add_paragraph()
p = doc.add_paragraph()
r = p.add_run("Luis Roberto Baldeón Sarmiento\nUniversidad Científica del Sur — Curso de Sistemas Operativos\n25 de noviembre de 2026")
r.font.size = Pt(9)
r.font.color.rgb = GRIS
r.italic = True

doc.save(OUT)
print("GENERADO:", OUT)
print("PARRAFOS:", len(doc.paragraphs), "TABLAS:", len(doc.tables))
