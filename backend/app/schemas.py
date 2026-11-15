from pydantic import BaseModel, Field

class SendRequest(BaseModel):
    sender: str
    receiver: str
    amount: float = Field(gt=0)
    pin: str = Field(min_length=4, max_length=8)

class MeshPacket(BaseModel):
    packetId: str
    ttl: int
    createdAt: int
    ciphertext: str
