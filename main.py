from pydantic import BaseModel
class Account(BaseModel):
    sold: float = 0.0
    userID: int
    name: str

def isTransferPossible(amount, firstAccount):
    return (firstAccount.sold > 0 and amount <= firstAccount.sold and amount > 0)

def transferMoney(amount, firstAccount, secondAccount):
    if isTransferPossible(amount, firstAccount):
        firstAccount.sold -= amount
        secondAccount.sold += amount
    else : 
        print("This account isn't sold enough to make the transfer")
    return firstAccount, secondAccount

firstAccount = Account(userID=1, name='testAccount')
secondAccount = Account(userID=2, name='testAccount2', sold=2000.0)

firstAccount, secondAccount = transferMoney(20, firstAccount, secondAccount)
print(f"firstAccount sold={firstAccount.sold} userID={firstAccount.userID} name='{firstAccount.name}'")
print(f"secondAccount sold={secondAccount.sold} userID={secondAccount.userID} name='{secondAccount.name}'")