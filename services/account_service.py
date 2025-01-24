from sqlalchemy.orm import Session
import db
from sqlalchemy import select

def addMoney(amount: float, session: Session, account: db.Account):
    if amount > 0:
        account.sold = account.sold + amount
        depotData = db.Deposit(sold=amount, userID=account.userID, accountID=account.id)
        session.add(depotData)
        session.add(account)
        session.commit()
        return "Money added successfully to account"
        
    else:
        return "Invalid amount, must be superior to 0"

def getAccount(session: Session, iban: str):
    account_query = select(db.Account).where(db.Account.iban == iban)
    return session.scalars(account_query).first()