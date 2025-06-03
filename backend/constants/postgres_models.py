from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, LargeBinary, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

from config.settings import FERNET_KEY, POSTGRES_CONNECTION_URL

cipher = Fernet(FERNET_KEY)

engine = create_engine(POSTGRES_CONNECTION_URL)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Bot(Base):
    __tablename__ = 'bots'

    bot_id = Column(BigInteger, primary_key=True)
    token = Column(LargeBinary, nullable=False)

    def set_token(self, plain_token: str):
        self.token = cipher.encrypt(plain_token.encode())

    def get_token(self) -> str:
        return cipher.decrypt(self.token).decode()

Base.metadata.create_all(engine)
