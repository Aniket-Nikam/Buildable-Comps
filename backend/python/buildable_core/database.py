from collections.abc import Callable

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


SessionFactory = Callable[[], Session]


def create_engine_and_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine_options = {"poolclass": StaticPool} if database_url.endswith(":memory:") else {}
    engine = create_engine(
        database_url, pool_pre_ping=True, connect_args=connect_args, **engine_options
    )
    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
