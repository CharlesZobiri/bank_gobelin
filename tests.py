import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from main import app
from db import get_db

engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_db] = override_get_session

client = TestClient(app)

@pytest.mark.run(order=1)
def test_auth_register():
    response = client.post(
        "/auth/register",
        json={
            "name": "test",
            "email": "test@example.com",
            "password": "thisisatest"
        }
    )
    assert response.status_code == 200
    assert response.json() == { "message": "User registered" }
    
@pytest.mark.run(order=2)
def test_auth_login():
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "thisisatest"
        }
    )
    assert response.status_code == 200
    assert response.json() == { "message": "User logged in" }
