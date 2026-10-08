from fastapi import Request


def get_current_user_id(request: Request) -> str:
    """Extracts the unique client session / user ID from request headers.
    Falls back to client IP or 'user_default'.
    """
    uid = request.headers.get("X-User-ID")
    if uid and uid.strip():
        return uid.strip()

    # Fallback to query parameter if present
    query_uid = request.query_params.get("user_id")
    if query_uid and query_uid.strip():
        return query_uid.strip()

    # Fallback to IP address to isolate devices
    if request.client and request.client.host:
        clean_ip = request.client.host.replace(":", "_").replace(".", "_")
        return f"user_ip_{clean_ip}"

    return "user_default"
