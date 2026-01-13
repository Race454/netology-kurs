import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, get_db
from app.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_advertisement(test_db):
    response = client.post(
        "/advertisement",
        json={
            "title": "Test Advertisement",
            "description": "Test Description",
            "price": 100.0,
            "author": "Test Author"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Advertisement"
    assert data["id"] is not None

def test_get_advertisement(test_db):
    create_response = client.post(
        "/advertisement",
        json={
            "title": "Test",
            "description": "Desc",
            "price": 50.0,
            "author": "Author"
        }
    )
    ad_id = create_response.json()["id"]
    response = client.get(f"/advertisement/{ad_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ad_id

def test_search_advertisements(test_db):
    for i in range(3):
        client.post(
            "/advertisement",
            json={
                "title": f"Ad {i}",
                "description": f"Description {i}",
                "price": 10.0 * (i + 1),
                "author": f"Author {i % 2}"
            }
        )
    
    response = client.get("/advertisement?author=Author 0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    response = client.get("/advertisement?min_price=15&max_price=25")
    assert response.status_code == 200