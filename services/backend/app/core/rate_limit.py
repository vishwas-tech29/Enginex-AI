"""Request-rate limiting.

Storage is in-memory by default — correct for a single worker process (and
for tests, which never run a real Redis instance) but NOT shared across the
`uvicorn --workers 4` processes docker-compose.prod.yml runs. Multi-worker/
multi-instance deployments need Redis-backed storage
(`storage_uri=settings.redis_url`) to actually share limits across
processes — a real follow-up, not implemented here, matching how
User.birth_year's lack of field-level encryption is flagged rather than
silently shipped as "encrypted" when it isn't.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
