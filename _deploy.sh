#!/bin/bash
set -e

# Variables to be provided as arguments
APP_DIR=$1
REPO_URL=$2
OPENAI_API_KEY=$3

echo "Starting deployment process..."

# Install required dependencies
apt-get update
apt-get install -y python3-venv python3-pip

# Remove old directory if exists
if [ -d "$APP_DIR" ]; then
  echo "Removing old application directory..."
  rm -rf $APP_DIR
fi

# Create directory and clone fresh repository
echo "Cloning fresh repository..."
mkdir -p $APP_DIR
git clone $REPO_URL $APP_DIR
cd $APP_DIR

# Create .env file with environment variables
echo "Creating .env file with environment variables..."
cat > .env << EOL
OPENAI_API_KEY=${OPENAI_API_KEY}
PRODUCTION=true
EOL

# Install dependencies
echo "Installing dependencies..."
./setup.sh

# Create systemd service file
echo "Creating systemd service file..."
cat > /tmp/ai-agent-service << 'EOL'
[Unit]
Description=AI Agent Conversation FastAPI App
After=network.target

[Service]
User=root
WorkingDirectory=APP_DIR
ExecStart=APP_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
EnvironmentFile=APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOL

# Replace APP_DIR placeholder with actual path
sed -i "s|APP_DIR|$APP_DIR|g" /tmp/ai-agent-service

# Install and start service
mv /tmp/ai-agent-service /etc/systemd/system/ai-agent-conversation.service
systemctl daemon-reload
systemctl enable ai-agent-conversation
systemctl restart ai-agent-conversation

echo "Deployment completed successfully!"
echo "Service status:"
systemctl status ai-agent-conversation --no-pager

# Print URL for checking API
echo "API should be available at: http://$(hostname -I | awk '{print $1}'):8000/docs"