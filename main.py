import db

def addMoney(amount: float, session: db.Session, user: db.User, account: db.Account):
    if (amount > 0):
        account.sold += amount
    else : 
        print("Invalid amount, must be superior to 0")
    db.update_account(session, user, account)
    return account

def getAccount(accounts, iban):
    for account in accounts:
        if account.iban == iban:
            return account
    return None

def isTransferPossible(amount, firstAccount):
    return (firstAccount.sold > 0 and amount <= firstAccount.sold and amount > 0)

def transferMoney(amount, firstAccount, secondAccount):
    if (firstAccount.iban == secondAccount.iban):
        print("Invalid transfert, the accounts are the same")
        return firstAccount, secondAccount
    if getAccount(accounts, secondAccount.iban) is None:
        print("The second account does not exist")
        return firstAccount, secondAccount
    if isTransferPossible(amount, firstAccount):
        firstAccount.sold -= amount
        secondAccount.sold += amount
    else : 
        print("This account isn't sold enough to make the transfer")
    return firstAccount, secondAccount

# Actual code
db.create_db_and_tables()
session : db.Session = db.create_session()
account = db.Account(name = "Dépôt", sold=120, userID=1, iban="0123456789012345678901234567890123")
user = db.User(email="ez@gmail.com", password="test")
session.add(account)
session.add(user)
session.commit()

addMoney(100, session, user, account)