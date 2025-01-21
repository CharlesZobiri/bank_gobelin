firstAccount = 450
secondAccount = 500.0

def transferMoney(amount, fromAccount, toAccount):
    if(isTransferPossible(amount, fromAccount)):
     return fromAccount - amount, toAccount + amount
    else:
     print("Transfer not possible")
     return fromAccount, toAccount

    

def isTransferPossible(amount, fromAccount):
    return (fromAccount > 0 and amount <= fromAccount and amount > 0)

 
print(firstAccount, secondAccount)
firstAccount, secondAccount = transferMoney(20, firstAccount, secondAccount)
print(firstAccount, secondAccount)