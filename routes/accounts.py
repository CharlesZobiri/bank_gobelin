
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import db
from models import AccountCreate, DepositBase,AccountBase,AccountsRecup
from services.account_service import addMoney
from services.transfer_service import transferMoney
from utils import generate_unique_iban
from sqlalchemy import or_

router = APIRouter()

@router.get("/users/{user_id}")
def read_user(user_id: int, db_session: Session = Depends(db.get_db)):
    user = db_session.query(db.User.name, db.User.email).filter(db.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": user.email, "name": user.name}

@router.post("/account/create")
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


@router.post("/account/infos")
def account_get(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}
    if account.isClosed:
        return{"error": "Account is closed"}

    return {"name": account.name, "sold": account.sold, "iban": account.iban, "created_at": account.created_at.strftime("%Y-%m-%d %H:%M:%S")}


@router.post("/account/deposit")
def account_deposit(body: DepositBase, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}
    if account.isClosed:
        return{"error": "Invalid deposit, this account was closed"}

    addMoney(body.sold, db_session, account)
    return {"message": "Money added to account"}



@router.post('/account/deposit_logs')
def account_deposit_logs(body: AccountCreate, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}

    deposit_query = db_session.query(db.Deposit.sold, db.Account.name).join(db.Account, db.Deposit.accountID == db.Account.id).filter(db.Deposit.accountID == account.id)
    deposits = db_session.scalars(deposit_query).all()
    return {"account_name": account.name, "deposits": deposits}


@router.post("/accounts/")
def accounts_get(body: AccountsRecup, db_session: Session = Depends(db.get_db)):
    user_query = db_session.query(db.User).where(db.User.id == body.userID)
    user = db_session.scalars(user_query).first()
    if user is None:
        return {"error": "User does not exist"}
    
    account_query = db_session.query(db.Account).where(db.Account.userID == body.userID, db.Account.isClosed==False).order_by(db.Account.created_at.desc())
    accounts = db_session.scalars(account_query).all()
    
    return {"accounts": [{"name": account.name, "sold": account.sold, "iban": account.iban, "date": account.created_at.strftime("%Y-%m-%d %H:%M:%S")} for account in accounts]}


@router.post("/account/close")
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


