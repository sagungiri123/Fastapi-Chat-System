# Chat Backend

FastAPI chat backend with PostgreSQL, Redis, Alembic migrations, and WebSocket chat support.

## Requirements

- Docker
- Docker Compose
- Git

## Start the server

From the project root, you can use the project helper script:

```bash
./start.sh
```

This script checks that your shell is in the Docker group and then runs:

```bash
docker compose up --build -d
docker compose exec -T app alembic upgrade head
```

If you prefer to do it manually:

```bash
docker compose up --build -d
```

If Docker returns a permission error like:

```bash
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

then add your user to the Docker group and start a new shell session:

```bash
sudo usermod -aG docker $USER
```

After logging out and back in, run:

```bash
docker compose up --build -d
```

Or, in the current shell only, use:

```bash
newgrp docker
```

This starts:
- app on http://localhost:8000
- PostgreSQL on localhost:5433
- Redis on localhost:6379

## Check the app

```bash
curl http://localhost:8000/
```

Expected response:

```json
{"message":"chat api running"}
```

## Run database migrations

If the database is new or schema changes were made:

```bash
docker compose exec -T app alembic upgrade head
```

Use `-T` so Docker does not try to attach a TTY in non-interactive shells. This avoids errors like:

```bash
cannot attach stdin to a TTY-enabled container because stdin is not a terminal
```

## Create a user

Use the helper script for safe user creation:

```bash
docker compose exec app python scripts/create_user.py alice alice@test.com secret
```

You can then log in through the form at:

```text
http://localhost:8000/static/index.html
```

## Useful commands

### Stop all services

```bash
docker compose down
```

### Stop and remove volumes

```bash
docker compose down -v
```

### View logs

```bash
docker compose logs -f app
```

### Restart the app container

```bash
docker compose restart app
```

## Notes

- The app uses PostgreSQL inside Docker, with host port `5433` to avoid conflicts with a local PostgreSQL install.
- The app container expects the DATABASE_URL env var to resolve to the internal Docker service name `db`.
- Alembic reads `DATABASE_URL` from the environment so migrations work in Docker without hardcoded localhost values.
