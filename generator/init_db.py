from sqlalchemy import inspect

from database.db import Base, engine
from database import models


def initialize_database():
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\nDatabase created successfully!")

    for table in tables:
        print(" -", table)

    print("\nTotal tables:", len(tables))


if __name__ == "__main__":
    initialize_database()