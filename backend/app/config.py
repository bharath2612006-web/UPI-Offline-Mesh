import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./upi_mesh.db")
PACKET_TTL = int(os.getenv("PACKET_TTL", "5"))
FRESHNESS_WINDOW_MS = int(os.getenv("FRESHNESS_WINDOW_MS", str(24 * 60 * 60 * 1000)))
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "86400"))
