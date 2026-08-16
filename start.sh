#!/usr/bin/env bash
set -e

# Start the chat backend in a Docker-enabled shell.
# This avoids needing to run `newgrp docker` manually in every terminal.

if ! id | grep -q 'docker'; then
  echo "You are not currently in the docker group."
  echo "Run: sudo usermod -aG docker \"\$USER\""
  echo "Then log out and log back in before using this script."
  exit 1
fi

cd "$(dirname "$0")"

docker compose up --build -d
docker compose exec -T app alembic upgrade head

echo "Project started successfully."
echo "Open: http://localhost:8000/static/index.html"
