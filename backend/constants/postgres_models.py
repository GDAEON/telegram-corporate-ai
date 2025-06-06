from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, ForeignKey, LargeBinary, BigInteger, Text, ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

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
    name = Column(Text, nullable=False)
    owner_id = Column(BigInteger, ForeignKey("owners.id", ondelete='CASCADE'), nullable=False)

    owner = relationship("Owner", back_populates="bots")

    def set_token(self, plain_token: str):
        self.token = cipher.encrypt(plain_token.encode())

    def get_token(self) -> str:
        return cipher.decrypt(self.token).decode()
    
    
class Owner(Base):
    __tablename__ = 'owners'

    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)

    bots = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")


Base.metadata.create_all(engine)
