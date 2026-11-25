# Guion para el Curso de Sistemas Operativos
## Dos tipos de servidor web: Apache y "el otro" (Nginx)

> Carpeta: `C:\Users\USER1\Desktop\test\cs2\linux ubuntu service\`  
> Simulador usado: `ubuntu_server_sim.py` + `launch_3_ventanas.py`  
> Nivel: Principiante / Intermedio  
> Idioma: Español (términos técnicos con significado sencillo)

---

## 1 · ¿Qué vamos a ver?

En este guion vamos a comparar **dos formas de servir páginas web** en un servidor Ubuntu:

| Tipo | Nombre | ¿Qué hace? |
|------|--------|------------|
| **A** | **Apache** | Es como el "recepcionista" de una casa: recibe visitas (peticiones web) y les entrega la página que piden. Es muy usado y fácil de configurar. |
| **B** | **Nginx** ("el otro") | Es como un "embajador muy rápido": también recibe visitas, pero lo hace de forma más ligera y eficiente cuando hay muchas personas al mismo tiempo. |

Ambos sirven para lo mismo (publicar páginas web), pero se configuran y se controlan con comandos distintos.

---

## 2 · Distribución A: Apache

### ¿Qué es Apache?

Apache es un **servidor web**. Piensa en él como un programa que se queda esperando en el servidor. Cuando alguien escribe una dirección en su navegador (por ejemplo `http://192.168.100.10`), Apache escucha, busca el archivo que pide y se lo envía.

### Comandos esenciales de Apache

| Comando | Qué significa en lenguaje sencillo | Para qué sirve |
|---------|-----------------------------------|----------------|
| `systemctl status apache2` | "¿Está prendido el recepcionista Apache?" | Te dice si el servidor web está funcionando o está apagado. |
| `systemctl start apache2` | "Enciende el recepcionista Apache" | Arranca el servidor web para que empiece a recibir visitas. |
| `systemctl stop apache2` | "Apaga el recepcionista Apache" | Detiene el servidor web; ya no recibe visitas. |
| `systemctl restart apache2` | "Reinicia el recepcionista Apache" | Apaga y prende otra vez (útil cuando cambias configuración). |
| `journalctl -u apache2` | "Lee el cuaderno de notas de Apache" | Muestra qué hizo Apache: errores, visitas, avisos. |
| `cat /var/www/html/index.html` | "Mira la página de bienvenida" | Muestra el contenido de la página principal que ven los visitantes. |

### Ejemplo práctico (en el simulador)

Desde la ventana del **Servidor** (`admin` / `luis`):

```
admin@pardoserver:~$ systemctl status apache2
```

Verás algo como:

```
● apache2.service - The Apache HTTP Server
     Active: active (running)
```

Eso significa: **Apache está prendido y funcionando**.

---

## 3 · Distribución B: Nginx ("el otro")

### ¿Qué es Nginx?

Nginx (se lee "engine-ex") es otro servidor web, parecido a Apache pero pensado para manejar **muchas visitas al mismo tiempo sin consumir mucha memoria**. Es común en sitios grandes y servidores de carga pesada.

### Comandos esenciales de Nginx

| Comando | Qué significa en lenguaje sencillo | Para qué sirve |
|---------|-----------------------------------|----------------|
| `systemctl status nginx` | "¿Está prendido el embajador Nginx?" | Te dice si Nginx está funcionando. |
| `systemctl start nginx` | "Enciende el embajador Nginx" | Arranca el servidor web Nginx. |
| `systemctl stop nginx` | "Apaga el embajador Nginx" | Detiene el servidor web Nginx. |
| `systemctl restart nginx` | "Reinicia el embajador Nginx" | Apaga y prende otra vez. |
| `nginx -t` | "Revisa que la configuración de Nginx no tenga errores" | Comprueba que todo esté bien escrito antes de aplicar cambios. |
| `cat /etc/nginx/nginx.conf` | "Mira el libro de reglas de Nginx" | Muestra cómo está configurado el servidor. |

### Ejemplo práctico (en el simulador)

Desde la ventana del **Servidor** (`admin` / `luis`):

```
admin@pardoserver:~$ systemctl status nginx
```

Si Nginx no está instalado en tu simulador, verás algo como:

```
Unit nginx.service could not be found.
```

Eso significa: **este servidor no tiene Nginx instalado**, solo tiene Apache (u otros servicios como ssh y smbd).

---

## 4 · Comparativa sencilla

| Pregunta | Apache | Nginx ("el otro") |
|----------|--------|-------------------|
| ¿Qué hace? | Sirve páginas web | Sirve páginas web |
| ¿Es difícil de configurar? | Medio fácil | Un poco más técnico |
| ¿Buen para muchas visitas a la vez? | Bien, pero consume más | Muy bien, consume menos |
| ¿Comando para ver estado? | `systemctl status apache2` | `systemctl status nginx` |
| ¿Comando para encender? | `systemctl start apache2` | `systemctl start nginx` |

---

## 5 · Simulación en los casos

Vamos a usar nuestro simulador con **3 ventanas** (Servidor, Atacante, Víctima) para ver ambos escenarios.

### Paso 0: Abrir las 3 ventanas

Desde una terminal de Windows, en la carpeta `linux ubuntu service\`:

```powershell
python launch_3_ventanas.py
```

Se abrirán 3 consolas:

| Ventana | Usuario | Contraseña | Rol |
|---------|---------|------------|-----|
| 1 | `admin` | `luis` | Servidor central |
| 2 | `operador1` | `op123` | Atacante |
| 3 | `operador2` | `op123` | Víctima |

---

### Caso A: Simular un servidor con Apache

**En la Ventana 1 (Servidor):**

```
admin@pardoserver:~$ servicios
```

Verás los 3 servicios simulados:

```
ssh      │ activo (running) │ puerto 22 │ OpenSSH secure shell server
apache2  │ activo (running) │ puerto 80 │ Apache HTTP Server
smbd     │ activo (running) │ puerto 445│ Samba SMB Daemon
```

**¿Qué significa esto?**
- **ssh**: permite entrar al servidor de forma remota y segura (puerto 22).
- **apache2**: es el servidor web encendido (puerto 80).
- **smbd**: sirve archivos en red tipo Windows (puerto 445).

Ahora revisa el estado detallado de Apache:

```
admin@pardoserver:~$ systemctl status apache2
```

Verás que dice `Active: active (running)`. Eso es Apache funcionando.

**Desde la Ventana 2 (Atacante) puedes probar conectividad:**

```
operador1@op1-endpoint:~$ ping 192.168.100.10
```

Esto envía señales al servidor para ver si responde. Si responde, el servidor está "vivo" en la red.

---

### Caso B: Simular un servidor con "el otro" (Nginx)

**En la Ventana 1 (Servidor):**

```
admin@pardoserver:~$ systemctl status nginx
```

Verás algo como:

```
Unit nginx.service could not be found.
```

**¿Qué significa?**
Que en este servidor simulado **no está instalado Nginx**. Solo está Apache. En un servidor real, podrías instalarlo, pero en nuestra simulación solo podemos mostrar qué comandos usarías si estuviera.

Si quisieras "fingir" que Nginx está activo (solo para practicar comandos), podrías ver los comandos del servidor con:

```
admin@pardoserver:~$ mapa
```

Y buscar en la lista los comandos de `systemctl`, `service`, `journalctl`, etc.

---

## 6 · Escenario de ataque y defensa (simulado)

Para entender cómo se protege un servidor web (Apache o Nginx), veamos qué pasa si el atacante intenta entrar:

**En la Ventana 2 (Atacante):**

```
operador1@op1-endpoint:~$ scan 192.168.100.22
```

Esto simula que el atacante escanea los puertos abiertos de la Víctima. Verás:

```
[ATAQUE] Escaneando 192.168.100.22...
  Puerto 22 (ssh):    abierto
  Puerto 80 (http):   abierto
  Puerto 445 (smbd):  abierto
```

**En la Ventana 3 (Víctima):**

```
operador2@op2-endpoint:~$ alertas
```

Verá que alguien la escaneó.

**En la Ventana 1 (Servidor):**

```
admin@pardoserver:~$ ver logs
```

El servidor ve TODO lo que pasó: quién escaneó a quién, cuándo, y si hubo éxito.

---

## 7 · Glosario de términos técnicos (fácil)

| Término | Significado sencillo |
|---------|---------------------|
| **Servidor web** | Programa que entrega páginas de internet cuando alguien las pide. |
| **Puerto** | Una "puerta" por donde entra y sale información del servidor (ej. 80 para web, 22 para ssh). |
| **systemctl** | Herramienta para encender, apagar o revisar servicios del sistema. |
| **Activo (running)** | El programa está prendido y funcionando. |
| **Inactivo (dead)** | El programa está apagado. |
| **Log / bitácora** | Cuaderno donde el servidor anota lo que hace (errores, visitas, etc.). |
| **Comprometido** | Cuando un atacante logró entrar o controlar parte del servidor. |
| **Escaneo (scan)** | Revisar qué puertas (puertos) tiene abiertas un servidor para buscar vulnerabilidades. |

---

## 8 · Resumen del guion para el profesor

1. Explicar qué es un servidor web (Apache vs Nginx).
2. Mostrar los comandos esenciales de cada uno con ejemplos reales.
3. Abrir las 3 ventanas del simulador.
4. Caso A: revisar `apache2` con `systemctl status apache2`.
5. Caso B: revisar que `nginx` no está instalado con `systemctl status nginx`.
6. Simular un ataque con `scan` desde el atacante y ver `alertas` en la víctima.
7. Ver todos los logs desde el servidor con `ver logs`.
8. Abrir el mapa de segmentos con `mapa segmentos` para ver quién está comprometido.

---

> **Nota:** Todo esto es una simulación educativa. No se instala ni se ejecuta software real peligroso. Los comandos de C2-DECT (`c2-server`, `build-*`, etc.) también están disponibles como comandos nativos si se quiere avanzar en la simulación de operaciones de seguridad.
