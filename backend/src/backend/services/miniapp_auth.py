import hashlib


def resolve_openid_from_code(code: str) -> str:
    normalized_code = code.strip()
    digest = hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()
    return f"mock-openid-{digest[:24]}"
