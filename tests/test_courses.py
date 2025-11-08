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

def test_add_course(client):
    payload = {
        "course_id": "1234",
        "course_name": "Robotics",
        "description": "Autonomous drones"
    }

    r = client.post("/api/add-course", json=payload)

    assert r.status_code == 201
    assert r.json()["course_id"] == "1234"

def test_get_all_courses_empty(client):
    r = client.get("/api/get-all-courses")
    assert r.status_code == 200
    assert r.json() == []


def test_get_course_by_id(client):
    # insert directly using POST endpoint
    payload = {"course_id": "1234", "course_name": "Robotics", "description": "Autonomous drones"}
    client.post("/api/add-course", json=payload)

    r = client.get("/api/get-course-by-id/1234")
    assert r.status_code == 200
    data = r.json()
    assert data["course_id"] == "1234"
    assert data["course_name"] == "Robotics"


def test_get_course_by_id_not_found(client):
    r = client.get("/api/get-course-by-id/9999")
    assert r.status_code == 404


def test_update_course(client):
    client.post("/api/add-course", json={"course_id": "2222", "course_name": "ML", "description": "ai sensors"})

    updated = {"course_id": "2222", "course_name": "ML UPDATED", "description": "updated desc"}
    r = client.put("/api/update-course-by-id/2222", json=updated)

    assert r.status_code == 200
    assert r.json() == {"message": "Course updated successful"}

    # verify update actually happened
    r2 = client.get("/api/get-course-by-id/2222")
    assert r2.json()["course_name"] == "ML UPDATED"


def test_delete_course(client):
    client.post("/api/add-course", json={"course_id": "3333", "course_name": "CICD", "description": "pipelines"})

    r = client.delete("/api/delete-course-by-id/3333")
    assert r.status_code == 200
    assert r.json() == {"message": "Deleted Course"}

    # verify deletion
    r2 = client.get("/api/get-course-by-id/3333")
    assert r2.status_code == 404
