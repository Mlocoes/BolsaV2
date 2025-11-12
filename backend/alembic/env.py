import asyncio
import logging
from logging.config import fileConfig
from sqlalchemy import pool, engine_from_config
from alembic import context
from app.core.config import settings
from app.db.models import Base

# Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure logging - skip if config file is missing or has issues
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        # If logging config is incomplete, setup basic logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('alembic.env')
        logger.info("Using basic logging configuration")

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
        await connection.run_sync(lambda conn: context.run_migrations())

def run_migrations_online():
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
