from cryptography.fernet import Fernet
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import (
    create_engine,
    Column,
    ForeignKey,
    LargeBinary,
    BigInteger,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from config.settings import FERNET_KEY, POSTGRES_CONNECTION_URL

cipher = Fernet(FERNET_KEY)

engine = create_engine(POSTGRES_CONNECTION_URL)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Bot(Base):
    __tablename__ = 'bots'

    id = Column(BigInteger, primary_key=True)
    token = Column(LargeBinary, nullable=False)
    name = Column(Text, nullable=False)
    ownerUuid = Column(LargeBinary, nullable=False)
    passUuid = Column(LargeBinary, nullable=False)
    webUrl = Column(LargeBinary, nullable=False)
    locale = Column(Text, nullable=False, default="en")
    isVerified = Column(Boolean, default=False, nullable=False)

    @hybrid_property
    def verified(self) -> bool:
        return self.isVerified

    @verified.setter
    def verified(self, value: bool) -> None:
        self.isVerified = bool(value)

    users = relationship("BotUser", back_populates="bot")
    pass_tokens = relationship(
        "PassToken",
        back_populates="bot",
        cascade="all, delete-orphan",
    )

    def set_token(self, plait_token: str):
        self.token = cipher.encrypt(plait_token.encode())

    def get_token(self) -> str:
        return cipher.decrypt(self.token).decode()
    
    def set_owner_uuid(self, plain_uuid: str):
        self.ownerUuid = cipher.encrypt(plain_uuid.encode())

    def get_owner_uuid(self) -> str:
        return cipher.decrypt(self.ownerUuid).decode()

    def set_pass_uuid(self, plain_uuid: str):
        self.passUuid = cipher.encrypt(plain_uuid.encode())

    def get_pass_uuid(self) -> str:
        return cipher.decrypt(self.passUuid).decode()
    
    def set_web_url(self, plain_url: str):
        self.webUrl = cipher.encrypt(plain_url.encode())

    def get_web_url(self) -> str:
        return cipher.decrypt(self.webUrl).decode()

    def set_locale(self, value: str):
        self.locale = value

    def get_locale(self) -> str:
        return self.locale


class PassToken(Base):
    __tablename__ = 'pass_tokens'

    uuid = Column(LargeBinary, primary_key=True)
    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    isUsed = Column(Boolean, default=False, nullable=False)

    bot = relationship('Bot', back_populates='pass_tokens')

    def set_uuid(self, plain_uuid: str):
        self.uuid = cipher.encrypt(plain_uuid.encode())

    def get_uuid(self) -> str:
        return cipher.decrypt(self.uuid).decode()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=True)
    surname = Column(Text, nullable=True)
    phone = Column(LargeBinary, nullable=True)

    bots = relationship("BotUser", back_populates="user")

    def set_phone(self, plain_phone: str):
        self.phone = cipher.encrypt(plain_phone.encode())

    def get_phone(self) -> str:
        return cipher.decrypt(self.phone).decode() 


class BotUser(Base):
    __tablename__ = 'bot_user'

    bot_id = Column(BigInteger, ForeignKey('bots.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)

    bot = relationship("Bot", back_populates="users")
    user = relationship("User", back_populates="bots")

    __table_args__ = (
        Index('ix_bot_user_bot_id_user_id', 'bot_id', 'user_id', unique=True),
    )

Base.metadata.create_all(engine)
