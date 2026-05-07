"""Drop and recreate all tables. Destructive — local use only."""
import _bootstrap  # noqa: F401

from app.db import Base, engine
import app.models  # noqa: F401  register models on Base


def main() -> None:
    print(f"Dropping all tables on {engine.url}...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating schema...")
    Base.metadata.create_all(bind=engine)
    print("Done.")


if __name__ == "__main__":
    main()
