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
    r = p.add_run("EC3 — Sustentación del Curso de Sistemas Operativos  |  Página ")
    r.font.size = Pt(8)
    r.font.color.rgb = GRIS
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    p._p.append(fld)


def add_header(section):
    p = section.header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("Laboratorio de Servicios Linux — linux ubuntu service")
    r.font.size = Pt(8)
    r.font.color.rgb = GRIS


# ---------------------------------------------------------------------------
# Documento base
# ---------------------------------------------------------------------------
doc = Document()
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
r = p.add_run("EVALUACIÓN CONTINUA 3")
r.bold = True
r.font.size = Pt(14)
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
    ("Curso", "Sistemas Operativos"),
    ("Estudiante", "Nakano-04"),
    ("Fecha", "25 de noviembre de 2026"),
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
rich_paragraph(doc, "Este documento compila y ordena todo el trabajo desarrollado para la "
              "Evaluación Continua 3 del curso de **Sistemas Operativos**. El laboratorio "
              "consiste en un **simulador educativo de Ubuntu 22.04 LTS que se ejecuta sobre "
              "Windows**, pensado para enseñar, sin riesgo real, cómo funcionan los servicios, "
              "los comandos, la red, los registros (logs) y un escenario de ataque/defensa.")
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
    "Apache vs Nginx y glossary de términos técnicos.",
    "Scripts de apoyo: ubuntu_win_sim.py, ubuntu_server_sim.py, launch_3_ventanas.py, "
    "mapa_segmentos.py, pagina_web_simuladores.html, logs/*.jsonl y configurar_apache2.sh.",
    "Todo el material es una **simulación segura**: los comandos destructivos nunca se ejecutan, "
    "solo se muestra qué haría el sistema operativo real.",
]:
    rich_paragraph(doc, bullet, style="List Bullet")

doc.add_heading("Índice del documento", level=1)
indice = [
    "1. Resumen ejecutivo",
    "2. Parte I — Diseño del simulador de terminal Ubuntu sobre Windows",
    "3. Parte II — Diseño del simulador de servidor Ubuntu (3 roles)",
    "4. Parte III — Guion completo para el curso de sistemas operativos",
    "5. Parte IV — Guion: dos tipos de servidor web (Apache y Nginx)",
    "6. Anexo A — Inventario de archivos desarrollados",
    "7. Anexo B — Ejecución rápida del laboratorio",
    "8. Anexo C — Conclusiones para la sustentación",
]
for item in indice:
    doc.add_paragraph(item, style="List Number")

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

doc.save(OUT)
print("GENERADO:", OUT)
print("PARRAFOS:", len(doc.paragraphs), "TABLAS:", len(doc.tables))
