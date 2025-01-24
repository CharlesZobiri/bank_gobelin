# TODO: Inheritance to avoid repetitions
from pydantic import BaseModel, EmailStr, constr
from datetime import datetime, timezone

class UserBase(BaseModel):
    name : str
    email: EmailStr
    password: constr(min_length=8)
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

    class Config:
        from_attributes = True
        
class AccountBase(BaseModel):
    name: str
    sold: float
    iban: constr(min_length=34, max_length=34)

    class Config:
        from_attributes = True

class AccountCreate(BaseModel):
    name: str
    userID: int

    class Config:
        from_attributes = True

class DepositBase(BaseModel):
    sold: float
    name: str
    userID: int

    class Config:
        from_attributes = True

class TransferBase(BaseModel):
    sold: float
    name: str
    iban: str
    userID: int

    class Config:
        from_attributes = True


class TransferLogBase(BaseModel):
    name : str
    userID: int

class TransferCancelled(BaseModel):
    userID: int
    transferID: int

class AccountsRecup(BaseModel):
    userID: int
    
class BeneficiaryBase(BaseModel):
    id: int
    name: str
    iban : str
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }


class BeneficiaryCreate(BaseModel):
    name: str
    iban: str
    userID: int
