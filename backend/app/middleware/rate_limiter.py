from slowapi import Limiter
from slowapi.util import get_remote_address

# Anti-DDoS and Brute-force protection
# Default limits: 100 per minute
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
