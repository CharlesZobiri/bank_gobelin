import hashlib
import db
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, constr
from fastapi import FastAPI, HTTPException, Depends
import random
import string
from sqlalchemy import select, literal, union, or_
from sqlalchemy.orm import Session, aliased
from fastapi_utilities import repeat_every
from datetime import datetime, timedelta


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

class TransferCancelled(BaseModel):
    userID: int
    transferID: int

class AccountsRecup(BaseModel):
    userID: int
    

@app.on_event("startup")
@repeat_every(seconds=5)
def processTransfers():
    print("Processing transfers...")
    db_session = next(db.get_db())
    
    min_timestamp = datetime.utcnow() - timedelta(seconds=10)

    completedTransfert_query = (
        db_session.query(db.Transfer)
        .filter(
            db.Transfer.status == db.TransfertStatus.PENDING,
            db.Transfer.created_at <= min_timestamp  
        )
    )
    transfers = db_session.scalars(completedTransfert_query).all()

    for transfer in transfers:
        sourceAccount = db_session.query(db.Account).filter(db.Account.id == transfer.sourceAccountID).first()
        targetAccount = db_session.query(db.Account).filter(db.Account.id == transfer.targetAccountID).first()

        if sourceAccount and targetAccount and sourceAccount.sold >= transfer.sold:
            sourceAccount.sold -= transfer.sold
            targetAccount.sold += transfer.sold
            db_session.add(sourceAccount)
            db_session.add(targetAccount)
            db_session.commit()

        transfer.status = db.TransfertStatus.COMPLETED
        db_session.add(transfer)
        db_session.commit()

    







        


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
        # sourceAccount.sold -= amount
        # targetAccount.sold += amount
        transferData = db.Transfer(sold=amount, userID=sourceAccount.userID, sourceAccountID=sourceAccount.id, targetAccountID=targetAccount.id)
        session.add(transferData)
        session.commit()
        return("Transfer done")
    else:
        return("This account isn't sold enough to make the transfer")

db.create_db_and_tables()

@app.get("/users/{user_id}")
def read_user(user_id: int, db_session: Session = Depends(db.get_db)):
    user = db_session.query(db.User.name, db.User.email).filter(db.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": user.email, "name": user.name}


@app.post("/auth/register")
def user_create(body: UserBase, db_session: Session = Depends(db.get_db)):
    user_query = db_session.query(db.User).where(db.User.email == body.email)
    user_exists = db_session.scalars(user_query).first()
    if user_exists:
        return {"error": "User already exists"}
    
    hash_password = hashlib.sha256(body.password.encode()).hexdigest()
    user = db.User(name= body.name, email=body.email, password=hash_password)
    db_session.add(user)
    db_session.commit()
    mainAccount = db.Account(name="Principal", sold=100, userID=user.id, iban=generate_unique_iban(db_session), isMain=True)
    db_session.add(mainAccount)
    db_session.commit()

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
        account_exists = db_session.scalars(account_query).first()
        if not account_exists:
            return iban
        

@app.post("/account/create")
def account_create(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    user_query = db_session.query(db.User).where(db.User.id == body.userID)
    user_exists = db_session.scalars(user_query).first()
    if not user_exists:
        return {"error": "User does not exist"}  
      
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account_exists = db_session.scalars(account_query).first()
    if account_exists:
        return {"error": "Account name already exists for this user"}

    newIban = generate_unique_iban(db_session)
    account_data = AccountBase(name=body.name, sold=0, iban=newIban)
    account = db.Account(name=account_data.name, sold=account_data.sold, userID=body.userID, iban=account_data.iban)
    db_session.add(account)
    db_session.commit()
    return {"message": "Account Opened"}


@app.post("/account/infos")
def account_get(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}
    if account.isClosed:
        return{"error": "Account is closed"}

    return {"name": account.name, "sold": account.sold, "iban": account.iban, "created_at": account.created_at.strftime("%Y-%m-%d %H:%M:%S")}



@app.post("/account/deposit")
def account_deposit(body: DepositBase, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}
    if account.isClosed:
        return("Invalid deposit, this account was closed")

    addMoney(body.sold, db_session, account)
    return {"message": "Money added to account"}



@app.post('/account/deposit_logs')
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
    if account.isClosed:
        return("Invalid transfer, the source account is closed")
    ibanClosed_query = db_session.query(db.Account).where(db.Account.iban == body.iban)
    accountClosed = db_session.scalars(ibanClosed_query).first()
    if accountClosed.isClosed:
        return("Invalid transfer, the target account is closed")


    message = transferMoney(db_session, body.sold, account, body.iban)
    return {"message": {message}}


@app.post('/account/transaction_logs')
def account_transaction_logs(body: TransferLogBase, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}

    
    TargetAccount = aliased(db.Account)
    
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
        .where(or_(db.Transfer.sourceAccountID == account.id, db.Transfer.targetAccountID == account.id))
    )
    
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
    
    combined_query = union(transfer_query, deposit_query)
    results = db_session.exec(combined_query).all()
    sorted_results = sorted(results, key=lambda x: x.created_at, reverse=True)
    
    transaction_logs = [
        {
            "amount": result.sold,
            "date": result.created_at.strftime("%Y-%m-%d %H:%M:%S") if result.created_at else None,
            "from_account": result.source_account,
            "to_account": result.target_account,
            "type": result.type
        }
        for result in sorted_results
    ]
    
    return {
        "account_name": account.name,
        "transactions": transaction_logs
    }


@app.post("/accounts/")
def accounts_get(body: AccountsRecup, db_session: Session = Depends(db.get_db)):
    user_query = db_session.query(db.User).where(db.User.id == body.userID)
    user = db_session.scalars(user_query).first()
    if user is None:
        return {"error": "User does not exist"}
    
    account_query = db_session.query(db.Account).where(db.Account.userID == body.userID, db.Account.isClosed==False).order_by(db.Account.created_at.desc())
    accounts = db_session.scalars(account_query).all()
    
    return {"accounts": [{"name": account.name, "sold": account.sold, "iban": account.iban, "date": account.created_at.strftime("%Y-%m-%d %H:%M:%S")} for account in accounts]}


@app.post("/account/close")
def account_close(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}
    if account.isMain:
        return {"error": "Main account cannot be closed"}
    pending_query = db_session.query(db.Transfer).where(or_(db.Transfer.sourceAccountID == account.id, db.Transfer.targetAccountID == account.id), db.Transfer.status == db.TransfertStatus.PENDING)
    pending_list = db_session.scalars(pending_query).all()
    if pending_list:
        return {"error": "Account has pending transfers"}
    account.isClosed = True
    transferMoney(db_session, account.sold, account, db_session.query(db.Account).filter(db.Account.isMain == True).first().iban)

    db_session.add(account)
    db_session.commit()
    return {"message": "Account closed"}


    
@app.post("/transfer/canceled")
def cancelledTransfert(body: TransferCancelled, db_session: Session = Depends(db.get_db)):
    transfer_query = db_session.query(db.Transfer).where(db.Transfer.id == body.transferID, db.Transfer.userID == body.userID)
    transfer = db_session.scalars(transfer_query).first()
    if transfer is None:
        return {"error": "Transfer not found"}
    if transfer.status == db.TransfertStatus.COMPLETED:
        return {"error": "Transfer already completed"}
    transfer.status = db.TransfertStatus.CANCELLED
    db_session.add(transfer)
    db_session.commit()
    return {"message": "Transfer cancelled"}