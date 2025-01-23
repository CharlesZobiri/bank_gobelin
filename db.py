from os import system
from sqlmodel import Field, SQLModel, create_engine, Session, update
from datetime import datetime
from enum import Enum

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password: str = Field(max_length=255)

class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sold: float = Field(default=0)
    userID: int = Field(foreign_key="user.id")
    iban: str = Field(max_length=34, unique=True, index=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isMain: bool = Field(default=False)
    isClosed: bool = Field(default=False)   

class Deposit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sold: float
    userID: int = Field(foreign_key="user.id")
    accountID: int = Field(foreign_key="account.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TransferStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Transfer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sold: float
    userID: int = Field(foreign_key="user.id")
    sourceAccountID: int = Field(foreign_key="account.id")
    targetAccountID: int = Field(foreign_key="account.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: TransferStatus = Field(default=TransferStatus.PENDING)

class Beneficiary(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    iban: str = Field(max_length=34, index=True)
    userID: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})

def create_session():
    return Session(engine)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_db():
    session = create_session()
    try:
        yield session
    finally:
        session.close()
