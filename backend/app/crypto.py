import base64, json, os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class ServerKeyHolder:
    def __init__(self):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()

    def public_key_b64(self):
        der = self.public_key.public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo)
        return base64.b64encode(der).decode()

class HybridCryptoService:
    def __init__(self, keys: ServerKeyHolder):
        self.keys = keys

    def encrypt(self, payload: dict) -> str:
        aes_key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
        encrypted = AESGCM(aes_key).encrypt(nonce, json.dumps(payload, separators=(",", ":")).encode(), None)
        wrapped_key = self.keys.public_key.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(), label=None))
        return base64.b64encode(wrapped_key + nonce + encrypted).decode()

    def decrypt(self, ciphertext_b64: str) -> dict:
        blob = base64.b64decode(ciphertext_b64, validate=True)
        key_size = self.keys.private_key.key_size // 8
        if len(blob) <= key_size + 12 + 16:
            raise ValueError("Ciphertext is too short")
        wrapped, nonce, encrypted = blob[:key_size], blob[key_size:key_size+12], blob[key_size+12:]
        aes_key = self.keys.private_key.decrypt(
            wrapped,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(), label=None))
        clear = AESGCM(aes_key).decrypt(nonce, encrypted, None)
        return json.loads(clear)

    @staticmethod
    def digest(ciphertext_b64: str) -> str:
        import hashlib
        return hashlib.sha256(base64.b64decode(ciphertext_b64, validate=True)).hexdigest()
