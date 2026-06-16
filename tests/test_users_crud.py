"""User CRUD via HTTP: bulk signup, list/get/update/soft-delete, DB checks, then hard-delete rows."""

from __future__ import annotations

import asyncio

from sqlalchemy import delete, func, select
from starlette.testclient import TestClient

from app.db.session import get_session_factory
from app.models.user import User

AUTH = "/api/v1/auth"
USERS = "/api/v1/users"

# Between 5 and 10 users as requested
NUM_USERS = 8


def _signup_json(i: int) -> dict:
    return {
        "email": f"crud{i}@example.com",
        "password": "password1",
        "full_name": f"CRUD User {i}",
    }


async def _db_count_all() -> int:
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(select(func.count()).select_from(User))
        return int(res.scalar_one())


async def _db_count_active() -> int:
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(
            select(func.count()).select_from(User).where(User.is_active.is_(True))
        )
        return int(res.scalar_one())


async def _db_hard_delete_all_users() -> None:
    """Remove every row from ``user`` (test cleanup — not an app API)."""
    factory = get_session_factory()
    async with factory() as session:
        await session.execute(delete(User))
        await session.commit()


def test_user_crud_many_users_persist_update_soft_delete_then_purge_db(client: TestClient) -> None:
    """Create NUM_USERS accounts, run CRUD, verify SQLite persistence, then hard-delete all rows."""

    # --- Create users (saved to DB via signup) ---
    for i in range(NUM_USERS):
        r = client.post(f"{AUTH}/signup", json=_signup_json(i))
        assert r.status_code == 201, r.text

    assert asyncio.run(_db_count_all()) == NUM_USERS
    assert asyncio.run(_db_count_active()) == NUM_USERS

    # --- Bearer token (any active user works for /users) ---
    token = client.post(
        f"{AUTH}/login",
        json={"email": "crud0@example.com", "password": "password1"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # --- LIST ---
    listed = client.get(f"{USERS}/list-users", headers=headers, params={"skip": 0, "limit": 100})
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == NUM_USERS
    emails = {row["email"] for row in body}
    assert emails == {f"crud{i}@example.com" for i in range(NUM_USERS)}

    # --- LIST pagination (skip 2, limit 3) ---
    page = client.get(f"{USERS}/list-users", headers=headers, params={"skip": 2, "limit": 3})
    assert page.status_code == 200
    assert len(page.json()) == 3

    # --- GET by id (first user id == 1 with empty DB before test) ---
    first = body[0]
    uid = first["id"]
    one = client.get(f"{USERS}/{uid}", headers=headers)
    assert one.status_code == 200
    assert one.json()["email"] == first["email"]
    assert one.json()["is_active"] is True

    # --- UPDATE (persist new full_name) ---
    target_id = body[3]["id"]
    put = client.put(
        f"{USERS}/{target_id}",
        headers=headers,
        json={"full_name": "Updated Via PUT"},
    )
    assert put.status_code == 200, put.text
    assert put.json()["full_name"] == "Updated Via PUT"

    again = client.get(f"{USERS}/{target_id}", headers=headers)
    assert again.status_code == 200
    assert again.json()["full_name"] == "Updated Via PUT"

    # --- SOFT DELETE (row remains, is_active False) ---
    del_id = body[5]["id"]
    deleted = client.delete(f"{USERS}/{del_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["is_active"] is False

    assert asyncio.run(_db_count_all()) == NUM_USERS
    assert asyncio.run(_db_count_active()) == NUM_USERS - 1

    still = client.get(f"{USERS}/{del_id}", headers=headers)
    assert still.status_code == 200
    assert still.json()["is_active"] is False

    # --- Hard delete all rows (true DB cleanup) ---
    asyncio.run(_db_hard_delete_all_users())
    assert asyncio.run(_db_count_all()) == 0
    assert asyncio.run(_db_count_active()) == 0
