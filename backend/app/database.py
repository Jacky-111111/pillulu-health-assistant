"""SQLAlchemy database setup and session management."""
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_PATH, DB_DIR

# Ensure data directory exists
Path(DB_DIR).mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_auth():
    """Add auth columns if missing. Create default user and assign orphan meds."""
    from app.models import User
    from app.services.auth import hash_password

    with engine.connect() as conn:
        try:
            r = conn.execute(text("PRAGMA table_info(users)"))
            cols = [row[1] for row in r]
            if "password_hash" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                conn.commit()
        except Exception:
            pass
        try:
            r = conn.execute(text("PRAGMA table_info(meds)"))
            cols = [row[1] for row in r]
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE meds ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                conn.commit()
        except Exception:
            pass
        for col, col_type in [("age", "INTEGER"), ("gender", "VARCHAR(32)"), ("height_cm", "INTEGER"), ("weight_kg", "INTEGER"), ("region", "VARCHAR(128)"), ("state", "VARCHAR(64)"), ("city", "VARCHAR(128)")]:
            try:
                r = conn.execute(text("PRAGMA table_info(users)"))
                cols = [row[1] for row in r]
                if col not in cols:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                    conn.commit()
            except Exception:
                pass
        for col, col_type in [
            ("canonical_name", "VARCHAR(255)"),
            ("image_url", "VARCHAR(1024)"),
            ("imprint", "VARCHAR(255)"),
            ("color", "VARCHAR(128)"),
            ("shape", "VARCHAR(128)"),
        ]:
            try:
                r = conn.execute(text("PRAGMA table_info(meds)"))
                cols = [row[1] for row in r]
                if col not in cols:
                    conn.execute(text(f"ALTER TABLE meds ADD COLUMN {col} {col_type}"))
                    conn.commit()
            except Exception:
                pass

    db = SessionLocal()
    try:
        auth_users = db.query(User).filter(User.password_hash.isnot(None)).first()
        if not auth_users:
            default = User(
                email="migrated@pillulu.local",
                password_hash=hash_password("changeme"),
            )
            db.add(default)
            db.commit()
            db.refresh(default)
            db.execute(text("UPDATE meds SET user_id = :uid WHERE user_id IS NULL"), {"uid": default.id})
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def init_db():
    """Create all tables and run migrations."""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _migrate_auth()
