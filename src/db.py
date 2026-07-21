from sqlalchemy import create_engine

from config import Config


def get_engine():
    connection_string = (
        f"postgresql+pg8000://{Config.DB_USER}:{Config.DB_PASSWORD}"
        f"@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
    )

    return create_engine(connection_string)
