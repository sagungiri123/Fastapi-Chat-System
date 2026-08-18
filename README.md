# Real-Time Chat Backend

Lightweight real-time chat backend built with FastAPI, WebSockets, PostgreSQL and Redis. It provides JWT auth, presence/typing indicators, DM rooms, paginated message history, and horizontal scaling via Redis Pub/Sub.

Key features

- JWT-based authentication (bcrypt password hashing)
- WebSocket-based real-time messaging
- Typing indicators and user presence
- Direct messages (DM rooms)
- Cursor-based message pagination (infinite scroll)
- PostgreSQL persistence and Alembic migrations
- Redis Pub/Sub for multi-process scaling

---

Getting started



1) Local development (virtualenv)

```bash
# create & activate venv
python3 -m venv venv
source venv/bin/activate

# install deps
pip install -r requirements.txt

# set environment variables in .env (see .env.example)
# run migrations
alembic upgrade head

# start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Configuration

Copy `.env.example` to `.env` (create if missing) and set the following variables:

- `DATABASE_URL` — PostgreSQL DSN, e.g. `postgresql+asyncpg://user:pass@localhost:5432/chatdb`
- `REDIS_URL` — Redis URL, e.g. `redis://localhost:6379/0`
- `SECRET_KEY` — JWT secret
- `ALGORITHM` (optional) — default `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES` (optional)

Database migrations

Use Alembic to run migrations or generate new ones:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Frontend

The minimal frontend is served from `app/static/index.html`. Open:

http://localhost:8000/static/index.html

Testing

- Unit and integration dependencies are listed in `requirements.txt`.
- A simple websocket integration test is in `tests/ws_integration_test.py`.

Run the integration test (server must be running):

```bash
source venv/bin/activate
python3 tests/ws_integration_test.py
```

Troubleshooting

- If `alembic upgrade head` fails because of multiple heads, run `alembic heads` to inspect and `alembic merge -m "merge heads" <rev1> <rev2>` to merge.
- Port 8000 already in use: stop other uvicorn instances or pick a different port.

Contributing

1. Fork the repo
2. Create a branch for your feature/fix
3. Run tests and update/add migrations where necessary
4. Open a PR with a clear description

License

This project is provided as-is. Add your license file if needed.
