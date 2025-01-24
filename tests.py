import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from main import app

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)

def override_get_db():
    session = Session(engine)
    try: yield session
    finally: session.close()

client = TestClient(app)

"""
Auth tests
"""

def test_auth_register():
    response = client.post("/auth/register", json={ "name": "test", "email": "test@example.com", "password": "thisisatest" })
    assert response.status_code == 200
    assert response.json() == { "message": "User registered" }
    
def test_auth_login():
    response = client.post("/auth/login", json={ "email": "test@example.com", "password": "thisisatest" })
    assert response.status_code == 200
    assert response.json() == { "message": "User logged in" }
        
def test_get_user():
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == { "name": "test", "email": "test@example.com" }
        
"""
Accounts tests
"""

def test_account_create():
    response = client.post("/account/create", json={"name": "Test", "userID": 1})
    assert response.status_code == 200
    assert response.json() == {"message": "Account Opened"}
        
def test_account_get():
    response = client.post("/account/infos", json={ "name": "Test", "userID": 1 })
    assert response.status_code == 200
    
    json_response = response.json()
    assert json_response["name"] == "Test"
    assert json_response["sold"] == 0
    
def test_account_deposit():
    response = client.post("/account/deposit", json={ "name": "Test", "userID": 1, "sold": 100 })
    assert response.status_code == 200
    assert response.json() == {"message": "Money added to account"}
    
def test_account_deposit_logs():
    response = client.post("/account/deposit_logs", json={ "name": "Test", "userID": 1 })
    assert response.status_code == 200
