from sqlalchemy import create_engine


def make_engine(url: str):
    if not url.startswith("postgresql+psycopg://"):
        raise ValueError("Bring Vene requires PostgreSQL with the psycopg driver.")
    return create_engine(
        url, pool_pre_ping=True, pool_size=5, max_overflow=0,
        connect_args={"connect_timeout": 2},
    )

