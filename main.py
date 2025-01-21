from pydantic import BaseModel
class Account(BaseModel):
    sold: float = 0.0
    userID: int
    iban: str
    name: str

firstAccount = Account(userID=1, name='testAccount', sold=30000.0, iban='RO123456789')
secondAccount = Account(userID=2, name='testAccount2', sold=2000.0, iban='RO987654321')
thirdAccount = Account(userID=3, name='testAccount3', sold=1000.0, iban='RO123456789')

accounts = [firstAccount, secondAccount, thirdAccount]


# Get function for account
def getAccount(accounts, iban):
    for account in accounts:
        if account.iban == iban:
            return account
    return None


# Transfer function
def isTransferPossible(amount, firstAccount):
    return (firstAccount.sold > 0 and amount <= firstAccount.sold and amount > 0)


# Transfer money function
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



firstAccount, secondAccount = transferMoney(20, firstAccount, firstAccount)
print(f"firstAccount sold={firstAccount.sold} userID={firstAccount.userID} name='{firstAccount.name}'")
print(f"secondAccount sold={secondAccount.sold} userID={secondAccount.userID} name='{secondAccount.name}'")


