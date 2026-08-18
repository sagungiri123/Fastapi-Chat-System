#  Real-Time Chat Backend

A high-performance, real-time chat application built with **FastAPI**, **WebSockets**, **PostgreSQL**, and **Redis**. Features include JWT authentication, typing indicators, user presence, private direct messages, and infinite message pagination.

---

##  Features

-  **JWT Authentication** – Secure login/register with bcrypt password hashing.
- **Real-time Messaging** – WebSocket-based bidirectional communication.
- **Typing Indicators** – See when others are typing in real-time.
- **User Presence** – Join/leave notifications for all room participants.
- **Private Direct Messages** – One-on-one encrypted (room-level) chats.
- **Message Pagination** – Infinite scroll with cursor-based loading.
- **Persistent Storage** – PostgreSQL with Alembic migrations.
- **Scalable Architecture** – Redis Pub/Sub for horizontal scaling.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.9+** – [Download](https://www.python.org/downloads/)
- **PostgreSQL 14+** – [Download](https://www.postgresql.org/download/)
- **Redis 6+** – [Download](https://redis.io/download/)
- **Git** – [Download](https://git-scm.com/downloads)




 1. Clone the Repository

Open your terminal and run:

```bash
git clone <your-repo-url>
cd chat-backend

2. To start the server:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload