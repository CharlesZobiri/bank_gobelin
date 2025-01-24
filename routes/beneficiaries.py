from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import db
from models import BeneficiaryCreate, BeneficiaryBase
from typing import List

router = APIRouter()

@router.post("/beneficiary/add")
def add_beneficiary(body: BeneficiaryCreate, db_session: Session = Depends(db.get_db)):
   
    existing_beneficiary = db_session.query(db.Beneficiary).filter(
        db.Beneficiary.userID == body.userID,
        db.Beneficiary.iban == body.iban
    ).first()
    
    if existing_beneficiary:
        raise HTTPException(status_code=400, detail="This beneficiary already exists")
    
    user_account = db_session.query(db.Account).filter(
        db.Account.userID == body.userID,
        db.Account.iban == body.iban
    ).first()
    
    if user_account:
        raise HTTPException(status_code=400, detail="The beneficiary account is the same as the user account")
    

    beneficiary_account = db_session.query(db.Account).filter(
        db.Account.iban == body.iban
    ).first()
    
    if not beneficiary_account:
        raise HTTPException(status_code=400, detail="Beneficiary acccount not found")
    
    
    new_beneficiary = db.Beneficiary(
        name=body.name,
        iban=body.iban,
        userID=body.userID
    )
    
    db_session.add(new_beneficiary)
    db_session.commit()
    
    return {"message": "Beneficiary added successfully"}

@router.get("/beneficiaries/{user_id}", response_model=List[BeneficiaryBase])
def get_beneficiaries(user_id: int, db_session: Session = Depends(db.get_db)):
    beneficiaries = db_session.query(db.Beneficiary).filter(db.Beneficiary.userID == user_id).all()
    return beneficiaries
