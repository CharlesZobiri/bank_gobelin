import hashlib
import db
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends

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
    sold: Decimal
    iban: constr(min_length=34, max_length=34)

    class Config:
        from_attributes = True

class DepositBase(BaseModel):
    sold: Decimal

    class Config:
        from_attributes = True

class TransferBase(BaseModel):
    sold: Decimal

    class Config:
        from_attributes = True

def addMoney(amount: float, session: Session, account: db.Account):
    if amount > 0:
        new_sold = account.sold + amount
        account_data = AccountBase(name=account.name, sold=new_sold, iban=account.iban)
        account.sold = account_data.sold
        session.commit()
    else:
        print("Invalid amount, must be superior to 0")
    return account

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




# user_query = select(db.User).where(db.User.email == "ez@gmail.com")
# user = session.scalars(user_query).first()
# if not user:
#     user_data = UserBase(name ="henri",email="ez@gmail.com", password="testpassword")
#     user = db.User(name=user_data.name, email=user_data.email, password=user_data.password)
#     session.add(user)

# account_query = select(db.Account).where(db.Account.iban == "0123456789012345678901234567890123")
# account = session.scalars(account_query).first()
# if not account:
#     account_data = AccountBase(name="Dépôt", sold=120, iban="0123456789012345678901234567890123")
#     account = db.Account(name=account_data.name, sold=account_data.sold, userID=user.id, iban=account_data.iban)
#     session.add(account)

# session.commit()

# addMoney(100, session, account)
# print(f"Account balance after adding money: {account.sold}")

# secondIban = "9876543210987654321098765432109876"
# second_account = getAccount(session, secondIban)
# if not second_account:
#     second_account_data = AccountBase(name="Épargne", sold=0, iban=secondIban)
#     second_account = db.Account(name=second_account_data.name, sold=second_account_data.sold, userID=user.id, iban=second_account_data.iban)
#     session.add(second_account)
#     session.commit()

# secondIban = "9876543210987654321098765432109876"
# transferMoney(session, 50, account, secondIban)
# second_account = getAccount(session, secondIban)
# print(f"First account balance after transfer: {account.sold}")
# print(f"Second account balance after transfer: {second_account.sold if second_account else 'N/A'}")


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
