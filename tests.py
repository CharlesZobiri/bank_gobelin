import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from main import app

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})
SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)

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
    json_response = response.json()
    assert json_response["message"] == "User logged in"
    assert json_response["access_token"] is not None
    assert json_response["token_type"] == "bearer"
        
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
    
    json_response = response.json()
    assert json_response["account_name"] == "Test"
    assert json_response["deposits"] is not None

def test_accounts_get():
    response = client.post("/accounts/", json={ "userID": 1 })
    assert response.status_code == 200
    
    json_response = response.json()
    assert json_response["accounts"] is not None

def test_account_close():
    client.post("/account/create", json={"name": "Test2", "userID": 1})
    response = client.post("/account/close", json={"name": "Test2", "userID": 1})
    assert response.status_code == 200
    assert response.json() == {"message": "Account closed"}

"""
Transfer tests
"""

def test_transfer():
    test_account = client.post("/account/infos", json={ "name": "Test", "userID": 1 }).json()
    response = client.post("/account/transfer", json={ "sold": 10, "name": "Principal", "iban": test_account["iban"], "userID": 1 })
    assert response.status_code == 200
    assert response.json()["message"] is not None
    
def test_transaction_logs():
    response = client.post("/account/transaction_logs", json={ "name": "Test", "userID": 1 })
    assert response.status_code == 200

    json_response = response.json()
    assert json_response["account_name"] == "Test"
    assert json_response["transactions"] is not None

def test_transfer_cancelled():
    last_transfer_id = client.post("/transfer/last").json()["id"]
    response = client.post("/transfer/canceled", json={ "userID": 1, "transferID": last_transfer_id })
    assert response.status_code == 200
    assert response.json() == {"message": "Transfer cancelled"}

def test_transfer_info():
    last_transfer_id = client.post("/transfer/last").json()["id"]
    response = client.post("/transfer/info", json={ "userID": 1, "transferID": last_transfer_id })
    assert response.status_code == 200

    json_response = response.json()
    assert json_response["amount"] == 10
    assert json_response["source_account"] is not "Unknown"
    assert json_response["target_account"] is not "Unknown"
    assert json_response["status"] == "cancelled"

"""
Beneficiaries tests
"""

def test_benificiaries_add():
    client.post("/auth/register", json={ "name": "test2", "email": "test2@example.com", "password": "thisisanothertest" })
    new_account = client.post("/account/infos", json={ "name": "Principal", "userID": 2 }).json()
    response = client.post("/beneficiary/add", json={ "name": "Titouan", "iban": new_account["iban"], "userID": 1})
    assert response.status_code == 200
    assert response.json() == {"message": "Bénéficiaire ajouté avec succès"}
    
def test_get_beneficiaries():
    response = client.get("/beneficiaries/1")
    assert response.status_code == 200
    
    json_response = response.json()
    beneficiary = json_response[0]
    assert beneficiary["id"] == 1
    assert beneficiary["name"] =="Titouan"
