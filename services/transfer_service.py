from sqlalchemy.orm import Session
import db
from .account_service import getAccount

def isTransferPossible(amount: float, firstAccount: db.Account):
    return firstAccount.sold > 0 and amount <= firstAccount.sold and amount > 0

def transferMoney(session: Session, amount: float, sourceAccount: db.Account, targetIban: str):
    if sourceAccount.iban == targetIban:
        return "error : Invalid transfer, the accounts are the same"
    if amount <= 0:
        return "error : Invalid amount, must be superior to 0"

    targetAccount = getAccount(session, targetIban)
    if targetAccount is None:
        return "error : This IBAN does not exist"
    
    if isTransferPossible(amount, sourceAccount):
        transferData = db.Transfer(sold=amount, userID=sourceAccount.userID, sourceAccountID=sourceAccount.id, targetAccountID=targetAccount.id)
        session.add(transferData)
        session.commit()
        return "Transfer done"
    else:
        return "error : This account isn't sold enough to make the transfer"