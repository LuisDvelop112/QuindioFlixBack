from contextlib import contextmanager
from typing import Generator

import oracledb

from app.config import settings

_pool: oracledb.ConnectionPool | None = None


def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=settings.oracle_user,
            password=settings.oracle_password,
            dsn=settings.oracle_dsn,
            min=1,
            max=5,
            increment=1,
        )


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_connection() -> Generator[oracledb.Connection, None, None]:
    if _pool is None:
        init_pool()
    conn = _pool.acquire()
    try:
        yield conn
    finally:
        _pool.release(conn)


@contextmanager
def get_cursor() -> Generator[oracledb.Cursor, None, None]:
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
