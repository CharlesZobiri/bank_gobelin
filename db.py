from os import system
from sqlmodel import Field, SQLModel, create_engine, Session, update

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password: str = Field(max_length=255)

class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sold: float
    userID: int = Field(foreign_key="user.id")
    iban: str = Field(max_length=34, unique=True, index=True)
    name: str = Field(index=True)

system("del database.db")
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_session():
    return Session(engine)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def update_account(session: Session, user: User, account: Account):
    session.exec(update(Account).where(account.userID == user.id).values(sold=account.sold, userID=account.userID, iban=account.iban, name=account.name)) 
    session.commit()
    session.refresh(account)