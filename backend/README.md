# UPI Offline Mesh — Python Backend

Python/FastAPI port of the architecture described in the reference repository's README. It preserves the same logical components and API routes: domain models, hybrid crypto, mesh simulator, idempotency, bridge ingestion, settlement, and dashboard.

> Educational simulation only. This is not an NPCI/UPI integration and must not be used to move real money. It models deferred settlement after a bridge device regains connectivity.

## Architecture mapping

| Original Spring Boot component | Python implementation |
|---|---|
| `Account`, `Transaction`, `MeshPacket`, `PaymentInstruction` | `app/models.py`, `app/schemas.py` |
| `ServerKeyHolder`, `HybridCryptoService` | `app/crypto.py` |
| `DemoService` | `app/services/demo.py` |
| `VirtualDevice`, `MeshSimulatorService` | `app/services/mesh.py` |
| `IdempotencyService` | `app/services/idempotency.py` |
| `SettlementService` | `app/services/settlement.py` |
| `BridgeIngestionService` | `app/services/ingestion.py` |
| `ApiController`, `DashboardController` | `app/main.py` |

## Run locally

Python 3.10+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Open `http://localhost:8080` for the demo dashboard and `http://localhost:8080/docs` for Swagger API docs.

## Demo sequence

1. Use the dashboard to inject a payment (default Alice to Bob, ₹500).
2. Run gossip round(s) to propagate the encrypted packet.
3. Click bridge upload to submit packets held by the internet-enabled bridge.
4. Refresh balances and transaction ledger. Re-uploading the same ciphertext is rejected as a duplicate.
5. Reset mesh to repeat.

Seed accounts:
- `alice@offline` — ₹5000
- `bob@offline` — ₹1000
- `carol@offline` — ₹2000

Demo PIN is hashed into the encrypted payload but is not authenticated against a real bank credential. Do not treat it as real PIN verification.

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Demo dashboard |
| GET | `/api/server-key` | RSA public key (base64 DER) |
| GET | `/api/accounts` | Account balances |
| GET | `/api/transactions` | Latest 20 ledger entries |
| GET | `/api/mesh/state` | Virtual device state |
| POST | `/api/demo/send` | Create/encrypt/inject demo payment |
| POST | `/api/mesh/gossip` | One mesh gossip round |
| POST | `/api/mesh/flush` | Upload bridge-held packets |
| POST | `/api/mesh/reset` | Reset devices and in-memory dedupe cache |
| POST | `/api/bridge/ingest` | Bridge ingestion endpoint |

### Bridge ingestion request

```json
{
  "packetId": "uuid",
  "ttl": 2,
  "createdAt": 1730000000000,
  "ciphertext": "base64-encoded-hybrid-ciphertext"
}
```

Optional headers: `X-Bridge-Node-Id`, `X-Hop-Count`.

## Security and implementation notes

- Hybrid encryption: fresh AES-256-GCM key per payment; AES key wrapped with RSA-OAEP/SHA-256.
- GCM authentication detects ciphertext tampering.
- SHA-256 of ciphertext is claimed before decryption; a lock makes the process-local claim atomic.
- The ledger has a unique constraint on `packet_hash` as a second line of defence.
- Freshness validation rejects timestamps older than 24 hours or in the future.
- Settlement updates debit, credit, and ledger in one database transaction.
- Default SQLite database is local and persistent. Set `DATABASE_URL` to use another SQLAlchemy-supported database.

## Important limitations / production hardening

This is a learning demo, not actual offline UPI. The mesh is software-simulated, the database defaults to SQLite, the idempotency cache is process-local, RSA keys are regenerated at startup, and there is no bridge authentication or bank/NPCI integration. A production design needs durable distributed idempotency (e.g. Redis SET NX plus database uniqueness), managed keys/HSM, authenticated bridge nodes, real device-to-device transport, proper PIN/payment authorization, fraud controls, audit logging, and regulatory integration.

The process-local idempotency cache is not shared between multiple worker processes. For a multi-instance deployment, use Redis or rely on a robust database-level idempotency claim in addition to the unique ledger constraint.

## Tests

```bash
pytest -q
```
