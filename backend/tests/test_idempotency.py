from concurrent.futures import ThreadPoolExecutor
from app.services.idempotency import IdempotencyService

def test_atomic_claim_only_once():
    service = IdempotencyService()
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: service.claim("same-hash"), range(12)))
    assert sum(results) == 1
