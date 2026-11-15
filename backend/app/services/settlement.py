from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.db import SessionLocal
from app.models import Account, Transaction

class SettlementService:
    def settle(self, instruction: dict, packet_hash: str):
        amount = float(instruction["amount"])
        sender_id, receiver_id = instruction["sender"], instruction["receiver"]
        if amount <= 0:
            return {"outcome": "INVALID", "reason": "Amount must be positive", "packetHash": packet_hash}
        try:
            with SessionLocal.begin() as db:
                # Lock rows on databases that support FOR UPDATE. SQLite serializes writes.
                sender = db.execute(select(Account).where(Account.upi_id == sender_id).with_for_update()).scalar_one_or_none()
                receiver = db.execute(select(Account).where(Account.upi_id == receiver_id).with_for_update()).scalar_one_or_none()
                if not sender or not receiver:
                    return {"outcome": "INVALID", "reason": "Unknown sender or receiver", "packetHash": packet_hash}
                if sender.balance < amount:
                    return {"outcome": "REJECTED", "reason": "Insufficient balance", "packetHash": packet_hash}
                sender.balance -= amount
                receiver.balance += amount
                sender.version += 1
                receiver.version += 1
                tx = Transaction(packet_hash=packet_hash, sender_upi=sender_id,
                                 receiver_upi=receiver_id, amount=amount, status="SETTLED")
                db.add(tx)
                db.flush()
                tx_id = tx.id
            return {"outcome": "SETTLED", "packetHash": packet_hash, "transactionId": tx_id}
        except IntegrityError:
            return {"outcome": "DUPLICATE_DROPPED", "packetHash": packet_hash, "reason": "Already settled"}
