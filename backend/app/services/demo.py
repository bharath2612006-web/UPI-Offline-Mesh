import time, uuid
from app.crypto import HybridCryptoService
from app.db import SessionLocal
from app.models import Account
from app.config import PACKET_TTL

class DemoService:
    def __init__(self, keys):
        self.crypto = HybridCryptoService(keys)

    def seed_accounts(self):
        with SessionLocal.begin() as db:
            if db.query(Account).count() == 0:
                db.add_all([
                    Account(upi_id="alice@offline", name="Alice", balance=5000.0),
                    Account(upi_id="bob@offline", name="Bob", balance=1000.0),
                    Account(upi_id="carol@offline", name="Carol", balance=2000.0),
                ])

    def create_packet(self, body, mesh):
        payload = body.model_dump()
        with SessionLocal() as db:
            sender = db.query(Account).filter_by(upi_id=payload["sender"]).first()
            receiver = db.query(Account).filter_by(upi_id=payload["receiver"]).first()
        if not sender or not receiver:
            raise ValueError("Unknown sender or receiver")
        # Demo-only PIN handling: never store or transmit a raw PIN in production.
        instruction = {
            "sender": payload["sender"], "receiver": payload["receiver"],
            "amount": payload["amount"], "pinHash": __import__("hashlib").sha256(payload["pin"].encode()).hexdigest(),
            "nonce": str(uuid.uuid4()), "signedAt": int(time.time() * 1000)
        }
        ciphertext = self.crypto.encrypt(instruction)
        packet = {"packetId": str(uuid.uuid4()), "ttl": PACKET_TTL,
                  "createdAt": int(time.time() * 1000), "ciphertext": ciphertext}
        mesh.inject(packet)
        return {"status": "INJECTED", "packet": packet}
