#!/bin/bash
set -e

APP_DIR=$1
REPO_URL=$2
OPENAI_API_KEY=$3
PORT=8000

echo "=== Installing system dependencies ==="
apt-get update
apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    ca-certificates \
    lsb-release \
    git \
    python3 \
    python3-venv \

echo "=== Installing Nginx 1.27.4 ==="
echo "deb http://nginx.org/packages/mainline/ubuntu $(lsb_release -cs) nginx" > /etc/apt/sources.list.d/nginx.list
curl -fsSL https://nginx.org/keys/nginx_signing.key | gpg --dearmor > /etc/apt/trusted.gpg.d/nginx.gpg
apt-get update
apt-get install -y nginx=1.27.4*

echo "=== Setting up firewall ==="
ufw allow 80/tcp
ufw allow 443/tcp

echo "=== Deploying application ==="
if [ -d "$APP_DIR" ]; then
  rm -rf $APP_DIR
fi

git clone $REPO_URL $APP_DIR
cd $APP_DIR

# Create SSL certificates before configuring nginx
echo "=== Creating SSL certificates ==="
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=165.22.92.253"

echo "=== Configuring Nginx ==="
cp $APP_DIR/config/nginx-fastapi.conf /etc/nginx/conf.d/app.conf
# Use IP address instead of domain
nginx -t

# Using the pre-installed dependencies from GitHub Actions
echo "=== Creating virtual environment ==="
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt

echo "PRODUCTION=true" > .env
echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env

echo "=== Creating systemd service ==="
cat > /etc/systemd/system/app.service << EOL
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $PORT
EnvironmentFile=$APP_DIR/.env
Restart=always
# Создаем /tmp директорию с правильными правами доступа
ExecStartPre=/bin/mkdir -p /tmp/ai-interview-temp
ExecStartPre=/bin/chown -R www-data:www-data /tmp/ai-interview-temp
ExecStartPre=/bin/chmod 755 /tmp/ai-interview-temp

[Install]
WantedBy=multi-user.target
EOL

echo "=== Starting services ==="
# Kill any processes using port 8000 before starting
if lsof -ti:$PORT > /dev/null; then
  echo "Killing existing processes on port $PORT"
  lsof -ti:$PORT | xargs kill -9
fi

# Make sure the service is stopped before restarting
systemctl stop app.service || true

systemctl daemon-reload
systemctl enable app.service nginx
systemctl restart app.service nginx

echo "=== Deployment complete ==="
IP_ADDRESS=$(curl -s ifconfig.me)
echo "Application URLs:"
echo "HTTP: http://$IP_ADDRESS"
echo "HTTPS: https://$IP_ADDRESS"
echo "API Docs: https://$IP_ADDRESS/docs"
