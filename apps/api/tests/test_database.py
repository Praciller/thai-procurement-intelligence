from app.database import _engine_args


def test_postgres_engine_disables_prepared_statements_for_poolers():
    args = _engine_args("postgresql+psycopg://postgres:postgres@example.supabase.co/postgres")

    assert args["pool_pre_ping"] is True
    assert args["connect_args"]["prepare_threshold"] is None


def test_sqlite_engine_allows_cross_thread_test_client_access():
    args = _engine_args("sqlite:///./test.db")

    assert args == {"connect_args": {"check_same_thread": False}}
