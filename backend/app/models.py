from sqlalchemy import String, Float, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.db import Base

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    upi_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    version: Mapped[int] = mapped_column(Integer, default=0)

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("packet_hash", name="uq_transaction_packet_hash"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    packet_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sender_upi: Mapped[str] = mapped_column(String(120))
    receiver_upi: Mapped[str] = mapped_column(String(120))
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
