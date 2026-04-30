"""
Rate-limiting placeholder.

Rate limiting helps slow down brute-force login attempts, password guessing, and
share-token scanning. A production version often uses Redis because it can count
requests across multiple running backend servers.
"""

from fastapi import Request


async def check_rate_limit(request: Request) -> None:
    """
    Placeholder dependency for future rate limiting.

    For now this function allows every request. Later, it can check the client IP
    address, route name, and recent request counts before deciding whether to
    allow or reject the request.
    """
    return None
