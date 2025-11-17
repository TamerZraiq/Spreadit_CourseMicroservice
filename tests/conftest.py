import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.models import Base
import app.database as database  # <-- needed to override engine + SessionLocal
from sqlalchemy.pool import StaticPool

# Use throwaway in-memory SQLite
TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,   # <-- THIS IS THE FIX
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Override the DB the app uses
database.engine = engine
database.SessionLocal = TestingSessionLocal
# Create tables on the SAME engine FastAPI now uses
Base.metadata.create_all(bind=engine)

@pytest.fixture
def client():
    # clean DB before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c  # <-- important for lifespan to run

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()