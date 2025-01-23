import db
from fastapi import FastAPI
from fastapi_utilities import repeat_every
from datetime import datetime, timedelta
from routes import auth_router, accounts_router, transfer_router, beneficiaries_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(transfer_router)
app.include_router(beneficiaries_router)


app = FastAPI()

app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(transfer_router)
app.include_router(beneficiaries_router)

db.create_db_and_tables()

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