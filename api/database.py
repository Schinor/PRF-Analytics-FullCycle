import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

load_dotenv()


def get_database_url() -> str | URL:
    """Retorna uma URL de conexão válida para PostgreSQL.

    ``DATABASE_URL`` é preferida para manter a API e o Alembic com a mesma
    configuração. Como alternativa, preserva as variáveis ``DB_*`` usadas pelo
    docker-compose do projeto.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql+psycopg2://", 1)
        return database_url.replace("postgres+psycog://", "postgresql+psycopg2://", 1)

    required_variables = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing_variables = [name for name in required_variables if not os.getenv(name)]
    if missing_variables:
        missing = ", ".join(missing_variables)
        raise RuntimeError(
            f"Configuração do banco incompleta. Defina DATABASE_URL ou: {missing}."
        )

    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )


engine = create_engine(get_database_url(), pool_pre_ping=True)
