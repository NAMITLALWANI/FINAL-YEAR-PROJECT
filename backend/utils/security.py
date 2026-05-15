import socket
import ipaddress
from urllib.parse import urlparse
from log_config import get_logger

logger = get_logger(__name__)

# List of blocked IP ranges (internal/private)
BLOCKED_NETWORKS = [
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fe80::/10'),
]

async def is_url_safe(url: str) -> bool:
    """
    Validate that the URL points to a public IP and uses HTTP/HTTPS.
    Protects against SSRF (Server-Side Request Forgery).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            logger.warning(f"Invalid scheme blocked: {parsed.scheme}")
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Resolve hostname to IPs
        # Note: In a production async environment, we'd use an async resolver.
        # For this prototype, socket.getaddrinfo is acceptable if called sparingly.
        addr_info = socket.getaddrinfo(hostname, None)
        
        for info in addr_info:
            ip_str = info[4][0]
            ip = ipaddress.ip_address(ip_str)
            
            # Check if IP is in any blocked network
            for network in BLOCKED_NETWORKS:
                if ip in network:
                    logger.warning(f"Blocked internal IP detected for {hostname}: {ip_str}")
                    return False
                    
        return True
    except Exception as e:
        logger.error(f"URL safety check failed for {url}: {e}")
        return False
