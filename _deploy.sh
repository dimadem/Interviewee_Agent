#!/bin/bash
set -e

APP_DIR=$1
REPO_URL=$2
OPENAI_API_KEY=$3
PORT=${4:-8000}  # Default port 8000 if not provided

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
ufw allow 'Nginx HTTP'

echo "=== Deploying application ==="
if [ -d "$APP_DIR" ]; then
  rm -rf $APP_DIR
fi

git clone $REPO_URL $APP_DIR
cd $APP_DIR

echo "=== Configuring Nginx ==="
cp $APP_DIR/config/nginx-fastapi.conf /etc/nginx/conf.d/app.conf
# Use IP address instead of domain
nginx -t

# Using the pre-installed dependencies from GitHub Actions
echo "=== Creating virtual environment ==="
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt --no-deps

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

[Install]
WantedBy=multi-user.target
EOL

echo "=== Starting services ==="
systemctl daemon-reload
systemctl enable app.service nginx
systemctl restart app.service nginx

echo "=== Deployment complete ==="
IP_ADDRESS=$(curl -s ifconfig.me)
echo "Application URL: http://$IP_ADDRESS"
echo "API Docs: http://$IP_ADDRESS/docs"
