#!/usr/bin/env python3
"""Small management script to create a user using the application models.

Usage (from repo root):
  sudo docker compose exec app python scripts/create_user.py <username> <email> <password>

This avoids shell-escaping issues with bcrypt hashes and reuses the app's
password-hashing implementation.
"""
import sys
from app.core.security import get_password_hash
from app.core.database import Base, AsyncSession, engine, AsyncSession as _ASession
from app.models.user import User
import asyncio


async def create_user(username: str, email: str, password: str):
    hashed = get_password_hash(password)
    async with _ASession(engine) as session:
        # check existing
        res = await session.execute(
            "SELECT id FROM users WHERE username = :u OR email = :e",
            {"u": username, "e": email},
        )
        if res.first():
            print("User already exists")
            return
        user = User(username=username, email=email, hashed_password=hashed)
        session.add(user)
        await session.commit()
        print(f"Created user {username}")


def main():
    if len(sys.argv) != 4:
        print("Usage: create_user.py <username> <email> <password>")
        sys.exit(2)
    username, email, password = sys.argv[1:4]
    asyncio.run(create_user(username, email, password))


if __name__ == "__main__":
    main()
