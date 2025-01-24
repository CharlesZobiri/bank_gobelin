from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import db
from models import UserBase, UserLogin
import hashlib
from utils import generate_iban, create_access_token, oauth2_scheme
router = APIRouter()


@router.post("/auth/register")
def user_create(body: UserBase, db_session: Session = Depends(db.get_db)):
    user_query = db_session.query(db.User).where(db.User.email == body.email)
    user_exists = db_session.scalars(user_query).first()
    if user_exists:
        return {"error": "User already exists"}
    
    hash_password = hashlib.sha256(body.password.encode()).hexdigest()
    user = db.User(name= body.name, email=body.email, password=hash_password)
    db_session.add(user)
    db_session.commit()
    
    iban: str
    while True:
        iban = generate_iban()
        account_query = db_session.query(db.Account).where(db.Account.iban == iban)
        if not db_session.scalars(account_query).first(): break
        
    mainAccount = db.Account(name="Principal", sold=100, userID=user.id, iban=iban, isMain=True)
    db_session.add(mainAccount)
    db_session.commit()

    return {"message": "User registered"}


@router.post("/auth/login")
def user_login(body: UserLogin, db_session: Session = Depends(db.get_db)):
    hash_password=hashlib.sha256(body.password.encode()).hexdigest()
    user_query = db_session.query(db.User).where(db.User.email == body.email, db.User.password == hash_password)
    user_exists = db_session.scalars(user_query).first()
    if not user_exists:
        return {"error": "Invalid credentials"}
    access_token = create_access_token(data={"sub": user_exists.email})
    return {"message": "User logged in", "access_token": access_token, "token_type": "bearer"}


    



