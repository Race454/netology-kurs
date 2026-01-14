import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

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
            "price": 100.50,
            "author": "Test Author"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Advertisement"
    assert float(data["price"]) == 100.50
    assert data["id"] is not None

def test_get_advertisement(test_db):
    create_response = client.post(
        "/advertisement",
        json={
            "title": "Test",
            "description": "Desc",
            "price": 50.00,
            "author": "Author"
        }
    )
    ad_id = create_response.json()["id"]
    
    response = client.get(f"/advertisement/{ad_id}")
    assert response.status_code == 200
    assert response.json()["id"] == ad_id

def test_delete_advertisement(test_db):
    create_response = client.post(
        "/advertisement",
        json={
            "title": "To Delete",
            "description": "Will be deleted",
            "price": 100.00,
            "author": "Author"
        }
    )
    ad_id = create_response.json()["id"]
    
    response = client.delete(f"/advertisement/{ad_id}")
    assert response.status_code == 204
    assert response.content == b""
    
    get_response = client.get(f"/advertisement/{ad_id}")
    assert get_response.status_code == 404

def test_search_advertisements_with_pagination(test_db):
    for i in range(5):
        client.post(
            "/advertisement",
            json={
                "title": f"Ad {i}",
                "description": f"Description {i}",
                "price": 10.0 * (i + 1),
                "author": f"Author {i % 2}"
            }
        )
    
    response = client.get("/advertisement?limit=2&skip=1")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    
    assert data["total"] == 5
    assert data["skip"] == 1
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    
    response = client.get("/advertisement?author=Author 0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    
    response = client.get("/advertisement?min_price=20&max_price=40")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3

def test_update_advertisement(test_db):
    create_response = client.post(
        "/advertisement",
        json={
            "title": "Original",
            "description": "Original Desc",
            "price": 100.00,
            "author": "Original Author"
        }
    )
    ad_id = create_response.json()["id"]
    
    update_response = client.patch(
        f"/advertisement/{ad_id}",
        json={"price": 90.50}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert float(data["price"]) == 90.50
    assert data["title"] == "Original"