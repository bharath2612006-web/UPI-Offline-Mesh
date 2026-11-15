from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from app.schemas import SendRequest, MeshPacket
from app.services.demo import DemoService
from app.services.mesh import MeshSimulatorService
from app.services.ingestion import BridgeIngestionService
from app.db import init_db, SessionLocal
from app.crypto import ServerKeyHolder

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.keys = ServerKeyHolder()
    app.state.demo = DemoService(app.state.keys)
    app.state.mesh = MeshSimulatorService()
    app.state.ingestion = BridgeIngestionService(app.state.keys)
    app.state.demo.seed_accounts()
    app.state.mesh.seed_devices()
    yield

app = FastAPI(title="UPI Offline Mesh - Python Backend", version="1.0.0", lifespan=lifespan)

# React/Vite development origin. Restrict production origins before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def dashboard():
    path = Path(__file__).parent / "templates" / "dashboard.html"
    return path.read_text()

@app.get("/api/server-key")
def server_key():
    return {"publicKey": app.state.keys.public_key_b64()}

@app.get("/api/accounts")
def accounts():
    from app.models import Account
    with SessionLocal() as db:
        return [{"id": a.id, "upiId": a.upi_id, "name": a.name, "balance": a.balance}
                for a in db.query(Account).order_by(Account.id).all()]

@app.get("/api/transactions")
def transactions():
    from app.models import Transaction
    with SessionLocal() as db:
        rows = db.query(Transaction).order_by(Transaction.id.desc()).limit(20).all()
        return [{"id": t.id, "sender": t.sender_upi, "receiver": t.receiver_upi,
                 "amount": t.amount, "status": t.status, "packetHash": t.packet_hash,
                 "createdAt": t.created_at.isoformat()} for t in rows]

@app.get("/api/mesh/state")
def mesh_state():
    return app.state.mesh.state()

@app.post("/api/demo/send")
def demo_send(body: SendRequest):
    try:
        return app.state.demo.create_packet(body, app.state.mesh)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/mesh/gossip")
def gossip():
    return app.state.mesh.gossip_round()

@app.post("/api/mesh/flush")
def flush():
    packets = app.state.mesh.bridge_packets()
    results = []
    for packet in packets:
        results.append(app.state.ingestion.ingest(packet))
    return {"uploaded": len(packets), "results": results}

@app.post("/api/mesh/reset")
def reset():
    app.state.mesh.reset()
    app.state.ingestion.reset_idempotency()
    return {"status": "RESET"}

@app.post("/api/bridge/ingest")
def ingest(packet: MeshPacket,
           bridge_node_id: Optional[str] = Header(default=None, alias="X-Bridge-Node-Id"),
           hop_count: Optional[int] = Header(default=0, alias="X-Hop-Count")):
    result = app.state.ingestion.ingest(packet, bridge_node_id, hop_count)
    return result
