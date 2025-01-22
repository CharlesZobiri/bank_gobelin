import hashlib
import db
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends
import random
import string
from datetime import datetime
from sqlalchemy import select, literal, union
from sqlalchemy.orm import Session, aliased

app = FastAPI()

class UserBase(BaseModel):
    name : str
    email: EmailStr
    password: constr(min_length=8)
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

    class Config:
        from_attributes = True
        
class AccountBase(BaseModel):
    name: str
    sold: float
    iban: constr(min_length=34, max_length=34)

    class Config:
        from_attributes = True

class AccountCreate(BaseModel):
    name: str
    userID: int

    class Config:
        from_attributes = True

class DepositBase(BaseModel):
    sold: float
    name: str
    userID: int

    class Config:
        from_attributes = True

class TransferBase(BaseModel):
    sold: float
    name: str
    iban: str
    userID: int

    class Config:
        from_attributes = True


class TransferLogBase(BaseModel):
    name : str
    userID: int
    


def addMoney(amount: float, session: Session, account: db.Account):
    if amount > 0:
        account.sold = account.sold + amount
        depotData = db.Deposit(sold=amount, userID=account.userID, accountID=account.id)
        session.add(depotData)
        session.add(account)
        session.commit()
        
    else:
        print("Invalid amount, must be superior to 0")

def getAccount(session: Session, iban: str):
    account_query = select(db.Account).where(db.Account.iban == iban)
    return session.scalars(account_query).first()

def isTransferPossible(amount: float, firstAccount: db.Account):
    return firstAccount.sold > 0 and amount <= firstAccount.sold and amount > 0

def transferMoney(session: Session, amount: float, sourceAccount: db.Account, targetIban: str):
    if sourceAccount.iban == targetIban:
        return("Invalid transfer, the accounts are the same")
    if amount <= 0:
        return("Invalid amount, must be superior to 0")

    targetAccount = getAccount(session, targetIban)
    if targetAccount is None:
        return("This IBAN does not exist")
    
    if isTransferPossible(amount, sourceAccount):
        sourceAccount.sold = sourceAccount.sold - amount
        targetAccount.sold = targetAccount.sold + amount
        transferData = db.Transfer(sold=amount, userID=sourceAccount.userID, sourceAccountID=sourceAccount.id, targetAccountID=targetAccount.id)
        session.add(transferData)
        session.commit()
        return("Transfer done")
    else:
        return("This account isn't sold enough to make the transfer")

db.create_db_and_tables()
session = db.create_session()

@app.get("/users/{user_id}")
def read_user(user_id: int, db_session: Session = Depends(db.get_db)):
    user = db_session.query(db.User.name, db.User.email).filter(db.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"name": user.name, "email": user.email}


@app.post("/auth/register")
def user_create(body: UserBase, db_session: Session = Depends(db.get_db)):
    user_query = db_session.query(db.User).where(db.User.email == body.email)
    user_exists = db_session.scalars(user_query).first()
    if user_exists:
        return {"error": "User already exists"}
    
    hash_password = hashlib.sha256(body.password.encode()).hexdigest()
    user = db.User(name= body.name, email=body.email, password=hash_password)
    session.add(user)
    session.commit()
    return {"message": "User registered"}


@app.post("/auth/login")
def user_login(body: UserLogin, db_session: Session = Depends(db.get_db)):
    hash_password=hashlib.sha256(body.password.encode()).hexdigest()
    user_query = db_session.query(db.User).where(db.User.email == body.email, db.User.password == hash_password)
    user_exists = db_session.scalars(user_query).first()
    if not user_exists:
        return {"error": "Invalid credentials"}
    return {"message": "User logged in"}


def generate_unique_iban(db_session: Session):
    while True:
        iban = ''.join(random.choices(string.digits, k=34))
        account_query = db_session.query(db.Account).where(db.Account.iban == iban)
        account_exists = session.scalars(account_query).first()
        if not account_exists:
            return iban
        

@app.post("/account/create")
def account_create(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    user_query = db_session.query(db.User).where(db.User.id == body.userID)
    user_exists = session.scalars(user_query).first()
    if not user_exists:
        return {"error": "User does not exist"}  
      
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account_exists = session.scalars(account_query).first()
    if account_exists:
        return {"error": "Account name already exists for this user"}

    newIban = generate_unique_iban(db_session)
    account_data = AccountBase(name=body.name, sold=0, iban=newIban)
    account = db.Account(name=account_data.name, sold=account_data.sold, userID=body.userID, iban=account_data.iban)
    session.add(account)
    session.commit()
    return {"message": "Account Opened"}


@app.post("/account/infos")
def account_get(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}

    return {"name": account.name, "sold": account.sold, "iban": account.iban}



@app.post("/account/deposit")
def account_deposit(body: DepositBase, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}

    addMoney(body.sold, db_session, account)
    return {"message": "Money added to account"}



@app.get('/account/deposit_logs')
def account_deposit_logs(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}

    deposit_query = db_session.query(db.Deposit.sold, db.Account.name).join(db.Account, db.Deposit.accountID == db.Account.id).filter(db.Deposit.accountID == account.id)
    deposits = db_session.scalars(deposit_query).all()
    return {"account_name": account.name, "deposits": deposits}



@app.post("/account/transfer")
def account_transfer(body: TransferBase, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}
    
    message = transferMoney(db_session, body.sold, account, body.iban)
    return {"message": {message}}


@app.post('/account/transaction_logs')
def account_transaction_logs(body: TransferLogBase, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}

    
    TargetAccount = aliased(db.Account)
    
    # Query for transfers
    transfer_query = (
        select(
            db.Transfer.sold,
            db.Transfer.created_at,
            db.Account.name.label('source_account'),
            TargetAccount.name.label('target_account'),
            literal('transfer').label('type')
        )
        .join(db.Account, db.Transfer.sourceAccountID == db.Account.id)
        .join(TargetAccount, db.Transfer.targetAccountID == TargetAccount.id)
        .where(db.Transfer.sourceAccountID == account.id)
    )
    
    # Query for deposits
    deposit_query = (
        select(
            db.Deposit.sold,
            db.Deposit.created_at,
            db.Account.name.label('source_account'),
            literal(None).label('target_account'),
            literal('deposit').label('type')
        )
        .join(db.Account, db.Deposit.accountID == db.Account.id)
        .where(db.Deposit.accountID == account.id)
    )
    
    # Combine and order the results
    combined_query = union(transfer_query, deposit_query).order_by(db.Transfer.created_at.desc())
    
    results = db_session.exec(combined_query).all()
    
    transaction_logs = [
        {
            "amount": result.sold,
            "date": result.created_at.strftime("%Y-%m-%d %H:%M:%S") if result.created_at else None,
            "from_account": result.source_account,
            "to_account": result.target_account,
            "type": result.type
        }
        for result in results
    ]
    
    return {
        "account_name": account.name,
        "transactions": transaction_logs
    }