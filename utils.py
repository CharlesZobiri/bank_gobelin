import random
import string
from sqlalchemy.orm import Session
import db

def generate_unique_iban(db_session: Session):
    while True:
        iban = ''.join(random.choices(string.digits, k=34))
        account_query = db_session.query(db.Account).where(db.Account.iban == iban)
        account_exists = db_session.scalars(account_query).first()
        if not account_exists:
            return iban
        