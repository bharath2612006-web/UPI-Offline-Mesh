from app.crypto import ServerKeyHolder, HybridCryptoService

def test_encrypt_decrypt_round_trip():
    crypto = HybridCryptoService(ServerKeyHolder())
    payload = {"sender":"alice@offline","amount":500,"nonce":"abc"}
    assert crypto.decrypt(crypto.encrypt(payload)) == payload

def test_tampered_ciphertext_rejected():
    crypto = HybridCryptoService(ServerKeyHolder())
    token = crypto.encrypt({"hello":"world"})
    import base64
    raw = bytearray(base64.b64decode(token))
    raw[-1] ^= 1
    import pytest
    with pytest.raises(Exception):
        crypto.decrypt(base64.b64encode(raw).decode())
