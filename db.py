from os import system
from sqlmodel import Field, SQLModel, create_engine, Session, update
from datetime import datetime

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password: str = Field(max_length=255)

class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sold: float = Field(default=0)
    userID: int = Field(foreign_key="user.id")
    iban: str = Field(max_length=34, unique=True, index=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Deposit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sold: float
    userID: int = Field(foreign_key="user.id")
    accountID: int = Field(foreign_key="account.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Transfer(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sold: float
    userID: int = Field(foreign_key="user.id")
    sourceAccountID: int = Field(foreign_key="account.id")
    targetAccountID: int = Field(foreign_key="account.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# system("del /Q database.db")
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

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