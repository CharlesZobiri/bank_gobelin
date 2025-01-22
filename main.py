import hashlib
import db
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends
import random
import string

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

    class Config:
        from_attributes = True

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

def transferMoney(session: Session, amount: float, firstAccount: db.Account, secondIban: str):
    if firstAccount.iban == secondIban:
        print("Invalid transfer, the accounts are the same")
        return firstAccount, None
    
    secondAccount = getAccount(session, secondIban)
    if secondAccount is None:
        print("The second account does not exist")
        return firstAccount, None
    
    if isTransferPossible(amount, firstAccount):
        new_sold_first = firstAccount.sold - amount
        new_sold_second = secondAccount.sold + amount
        
        first_account_data = AccountBase(name=firstAccount.name, sold=new_sold_first, iban=firstAccount.iban)
        second_account_data = AccountBase(name=secondAccount.name, sold=new_sold_second, iban=secondAccount.iban)
        
        firstAccount.sold = first_account_data.sold
        secondAccount.sold = second_account_data.sold
        session.commit()
    else:
        print("This account isn't sold enough to make the transfer")
    
    return firstAccount, secondAccount

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
    user_exists = session.scalars(user_query).first()
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
    user_exists = session.scalars(user_query).first()
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




