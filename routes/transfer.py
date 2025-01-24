from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import db
from models import TransferBase, TransferLogBase, TransferCancelled
from services.transfer_service import transferMoney
from sqlalchemy import select, literal, union, or_
from sqlalchemy.orm import Session, aliased

router = APIRouter()

@router.post("/account/transfer")
def account_transfer(body: TransferBase, db_session: Session = Depends(db.get_db)):
    account_query = db_session.query(db.Account).where(db.Account.name == body.name, db.Account.userID == body.userID)
    account = db_session.scalars(account_query).first()
    if account is None:
        return {"error": "Account not found"}
    if account.isClosed:
        return{"error": "Invalid transfer, the source account is closed"}
    ibanClosed_query = db_session.query(db.Account).where(db.Account.iban == body.iban)
    accountClosed = db_session.scalars(ibanClosed_query).first()
    if accountClosed.isClosed:
        return{"error": "Invalid transfer, the target account is closed"}

    message = transferMoney(db_session, body.sold, account, body.iban)
    return {"message": {message}}

@router.post('/account/transaction_logs')
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
            literal('transfer').label('type'),
            db.Transfer.status
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
            literal('deposit').label('type'),
            literal(None).label('status')
        )
        .join(db.Account, db.Deposit.accountID == db.Account.id)
        .where(db.Deposit.accountID == account.id)
    )
    
    combined_query = union(transfer_query, deposit_query)
    results = db_session.exec(combined_query).all()
    sorted_results = sorted(results, key=lambda x: x.created_at, reverse=True)
    
    transaction_logs = []
    for result in sorted_results:
        log = {
            "amount": result.sold,
            "date": result.created_at.strftime("%Y-%m-%d %H:%M:%S") if result.created_at else None,
            "from_account": result.source_account,
            "type": result.type
        }
        if result.type == 'transfer':
            log["to_account"] = result.target_account
            log["status"] = result.status.value if result.status else None
        
        transaction_logs.append(log)
    
    return {
        "account_name": account.name,
        "transactions": transaction_logs
    }
    
@router.post("/transfer/canceled")
def cancelledTransfer(body: TransferCancelled, db_session: Session = Depends(db.get_db)):
    transfer_query = db_session.query(db.Transfer).where(db.Transfer.id == body.transferID, db.Transfer.userID == body.userID)
    transfer = db_session.scalars(transfer_query).first()
    if transfer is None:
        return {"error": "Transfer not found"}
    if transfer.status == db.TransferStatus.COMPLETED:
        return {"error": "Transfer already completed"}
    transfer.status = db.TransferStatus.CANCELLED
    db_session.add(transfer)
    db_session.commit()
    return {"message": "Transfer cancelled"}

@router.post("/transfer/info")
def transfer_info(body: TransferCancelled, db_session: Session = Depends(db.get_db)):
    transfer_query = db_session.query(db.Transfer).where(db.Transfer.id == body.transferID, db.Transfer.userID == body.userID)
    transfer = db_session.scalars(transfer_query).first()
    if transfer is None:
        return {"error": "Transfer not found"}
    
    source_account = db_session.query(db.Account).filter(db.Account.id == transfer.sourceAccountID).first()
    target_account = db_session.query(db.Account).filter(db.Account.id == transfer.targetAccountID).first()
    
    return {
        "amount": transfer.sold,
        "source_account": source_account.name if source_account else "Unknown",
        "target_account": target_account.name if target_account else "Unknown",
        "status": transfer.status.value
    }

@router.post("/transfer/last")
def get_last_transfer(db_session: Session = Depends(db.get_db)):
    last_transfer = db_session.query(db.Transfer).order_by(db.Transfer.created_at.desc()).first()

    if last_transfer is None:
        return {"error": "No transfers found"}

    return {"id": last_transfer.id}

