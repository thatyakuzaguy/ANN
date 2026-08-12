from alembic import context


def run_migrations_offline() -> None:
    context.configure(url="sqlite:///./game.db")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    run_migrations_offline()


run_migrations_online()
