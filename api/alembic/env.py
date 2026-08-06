from logging.config import fileConfig
import os
from dotenv import load_dotenv

from alembic import context

# 1. Carrega as variáveis de ambiente do .env
load_dotenv()

# 2. Importa o Base e a mesma configuração de conexão usada pela API.
from models import Base, UF, BR, Regional, Delegacia, UOP, Arquivo_Carregado, Acidentes_Registrados
from database import engine, get_database_url

# Alembic Config object
config = context.config

# 3. Nunca use o placeholder de alembic.ini: API e migrações devem conectar
# ao mesmo banco, seja por DATABASE_URL, seja pelas variáveis DB_*.
config.set_main_option("sqlalchemy.url", str(get_database_url()))

# Configuração de Logs
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. Vincula os metadados do SQLAlchemy para suporte ao --autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações no modo 'online'."""
    # Reutiliza a URL tipada da API. Converter a URL para ConfigParser e criar
    # outro engine pode alterar senhas com caracteres especiais.
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
