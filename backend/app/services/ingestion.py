from datetime import datetime, timezone
from app.crypto import HybridCryptoService
from app.services.idempotency import IdempotencyService
from app.services.settlement import SettlementService
from app.config import FRESHNESS_WINDOW_MS

class BridgeIngestionService:
    def __init__(self, keys):
        self.crypto = HybridCryptoService(keys)
        self.idempotency = IdempotencyService()
        self.settlement = SettlementService()

    def ingest(self, packet, bridge_node_id=None, hop_count=0):
        try:
            packet = packet.model_dump() if hasattr(packet, "model_dump") else dict(packet)
            packet_hash = self.crypto.digest(packet["ciphertext"])
        except Exception:
            return {"outcome": "INVALID", "reason": "Malformed ciphertext"}
        if not self.idempotency.claim(packet_hash):
            return {"outcome": "DUPLICATE_DROPPED", "packetHash": packet_hash}
        try:
            instruction = self.crypto.decrypt(packet["ciphertext"])
            signed_at = int(instruction["signedAt"])
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            if signed_at > now_ms or now_ms - signed_at > FRESHNESS_WINDOW_MS:
                return {"outcome": "INVALID", "packetHash": packet_hash, "reason": "Packet expired or timestamp is in the future"}
            if not instruction.get("nonce"):
                return {"outcome": "INVALID", "packetHash": packet_hash, "reason": "Missing nonce"}
            return self.settlement.settle(instruction, packet_hash)
        except Exception:
            return {"outcome": "INVALID", "packetHash": packet_hash, "reason": "Decryption or payload validation failed"}

    def reset_idempotency(self):
        self.idempotency.reset()
