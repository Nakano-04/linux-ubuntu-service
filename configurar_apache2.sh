#!/usr/bin/env bash
# =============================================================================
# EC3 - Laboratorio de servicios basado en Linux
# configurar_apache2.sh
#
# Instala, habilita, configura y verifica el servicio Apache2 (puerto 80) en
# Ubuntu 22.04 LTS. Disenado para ser mostrado en la demostracion en vivo.
#
# Uso:
#   sudo bash configurar_apache2.sh
# =============================================================================

set -euo pipefail

SERVICE="apache2"
PORT=80
INDEX_FILE="/var/www/html/index.html"

echo "============================================================"
echo " EC3 | Apache2 service configuration - Ubuntu 22.04 LTS"
echo "============================================================"

echo ""
echo "[1/6] Updating package index..."
sudo apt-get update -y

echo ""
echo "[2/6] Installing Apache2..."
sudo apt-get install -y "$SERVICE"

echo ""
echo "[3/6] Enabling and starting the service..."
sudo systemctl enable "$SERVICE"
sudo systemctl restart "$SERVICE"

echo ""
echo "[4/6] Allowing port $PORT/tcp through UFW (only if firewall is active)..."
if sudo ufw status | grep -qi "active"; then
    sudo ufw allow "$PORT/tcp" comment "Apache2 HTTP"
    sudo ufw status | grep "$PORT"
else
    echo "UFW is inactive -> firewall rule skipped (not needed in the lab)."
fi

echo ""
echo "[5/6] Creating a custom test page..."
sudo tee "$INDEX_FILE" > /dev/null <<'HTML'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>EC3 - Apache2 Lab</title>
</head>
<body>
    <h1>Apache2 is working</h1>
    <p>EC3 Linux Services Lab - configured with configurar_apache2.sh</p>
</body>
</html>
HTML

echo ""
echo "[6/6] Verifying service, port, HTTP response and logs..."
sudo systemctl status "$SERVICE" --no-pager
echo "--- Listening sockets on port $PORT ---"
sudo ss -tulpn | grep ":${PORT}" || echo "WARNING: nothing listening on port $PORT"
echo "--- HTTP response from localhost ---"
curl -fsS "http://127.0.0.1" | head -n 8
echo "--- Last 10 lines of the Apache2 journal ---"
sudo journalctl -u "$SERVICE" --no-pager -n 10

echo ""
echo "============================================================"
echo " DONE: Apache2 is active (running) on port $PORT"
echo "============================================================"
