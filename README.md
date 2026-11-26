# Laboratorio de Servicios Linux — EC3

**Universidad Científica del Sur** · Curso de **Sistemas Operativos**  
**Alumno:** Luis Roberto Baldeón Sarmiento  
**Evaluación:** Evaluación Continua 3 (EC3) · 25 de noviembre de 2026  
**Repositorio:** privado — `Nakano-04/linux-ubuntu-service`

---

## Descripción

Laboratorio educativo basado en **Ubuntu 22.04 LTS simulado sobre Windows**. Permite estudiar,
sin riesgo real, los servicios del sistema operativo (ssh, apache2, smbd), los comandos
esenciales y su equivalente Windows, la red, los logs forenses y un escenario de
ataque/defensa con tres roles: **Servidor, Atacante y Víctima**.

> Uso exclusivamente educativo y de testing autorizado. Los comandos destructivos nunca
> se ejecutan: solo se muestra el "servicio a hacer" y se registra en el log.

---

## Documentación principal

| Archivo | Descripción |
|---------|-------------|
| [DOCUMENTO_SUSTENTACION_CURSO_SO.docx](DOCUMENTO_SUSTENTACION_CURSO_SO.docx) | Word de sustentación: marco teórico, secuencia didáctica, matriz de cobertura, preguntas, guion en inglés y anexos. |
| [DISEÑO.md](DISEÑO.md) | Diseño de la terminal Ubuntu indexada a Windows: variantes, IPs, rama de decisión, honeypot y logs forenses. |
| [DISEÑO_SERVER.md](DISEÑO_SERVER.md) | Diseño del servidor de 3 roles: servicios, comandos de ataque, logs compartidos y mapa de segmentos. |
| [GUION_CURSO_SO.md](GUION_CURSO_SO.md) | Guion completo para el curso: servicios, comandos y escenarios A–D. |
| [GUION_DISTRIBUCIONES.md](GUION_DISTRIBUCIONES.md) | Guion comparativo Apache vs Nginx y escenarios de clase. |
| [generar_documento_sustentacion.py](generar_documento_sustentacion.py) | Generador del documento Word a partir de los cuatro `.md`. |

---

## Archivos desarrollados

| Archivo | Descripción |
|---------|-------------|
| [ubuntu_win_sim.py](ubuntu_win_sim.py) | Simulador de terminal Ubuntu sobre Windows (standard/apt, honeypot, logs). |
| [ubuntu_server_sim.py](ubuntu_server_sim.py) | Simulador de servidor con roles Servidor, Atacante y Víctima. |
| [launch_3_ventanas.py](launch_3_ventanas.py) | Abre las tres consolas de Windows en procesos independientes. |
| [mapa_segmentos.py](mapa_segmentos.py) | Ventana separada con el estado de compromiso de la red. |
| [pagina_web_simuladores.html](pagina_web_simuladores.html) | Página de prueba servida por Apache en el puerto 80. |
| [configurar_apache2.sh](configurar_apache2.sh) | Instala, habilita y verifica Apache2 en Ubuntu (puerto 80). |
| [logs/shared_logs.jsonl](logs/shared_logs.jsonl) | Log de auditoría compartido entre los tres roles. |
| [logs/estado_red.json](logs/estado_red.json) | Estado de compromiso de los segmentos. |

---

## Ejecución rápida

```powershell
cd "C:\Users\USER1\Desktop\test\cs2\linux ubuntu service"
python launch_3_ventanas.py
```

Logins:

| Rol | Usuario | Contraseña | IP simulada |
|-----|---------|------------|-------------|
| Servidor | `admin` | `luis` | 192.168.100.10 |
| Atacante | `operador1` | `op123` | 192.168.100.21 |
| Víctima | `operador2` | `op123` | 192.168.100.22 |

Comandos clave: `servicios`, `systemctl status apache2`, `ip a`, `ver logs`,
`scan 192.168.100.22`, `exploit 192.168.100.22`, `alertas`, `mapa segmentos`.

En Ubuntu/VM real: `sudo bash configurar_apache2.sh`.

---

## Entregable EC3

1. Exposición oral en inglés de **1,5–3 minutos**.
2. Video de **6–10 minutos**, en línea, con el rostro visible, explicando la
   configuración de Apache2.
3. Demostración del trabajo **directamente desde la terminal del laboratorio**
   (no solo PDF o modo gráfico).

El guion detallado en inglés está en el **Anexo D** del documento Word.
