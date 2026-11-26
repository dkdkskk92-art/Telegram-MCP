import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    session: str
    access_token: str
    send_allowlist: frozenset[int]
    host: str
    port: int


def load_settings() -> Settings:
    names = ("TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_SESSION", "MCP_ACCESS_TOKEN")
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))

    try:
        api_id = int(os.environ["TELEGRAM_API_ID"])
        port = int(os.getenv("PORT", "8000"))
        allowlist = frozenset(
            int(value.strip())
            for value in os.getenv("TELEGRAM_SEND_ALLOWLIST", "").split(",")
            if value.strip()
        )
    except ValueError as exc:
        raise RuntimeError("API ID, PORT and allowlist entries must be integers") from exc

    if api_id <= 0 or not 1 <= port <= 65535:
        raise RuntimeError("Invalid API ID or PORT")

    token = os.environ["MCP_ACCESS_TOKEN"]
    if len(token) < 32:
        raise RuntimeError("MCP_ACCESS_TOKEN must be at least 32 characters")

    return Settings(
        api_id=api_id,
        api_hash=os.environ["TELEGRAM_API_HASH"],
        session=os.environ["TELEGRAM_SESSION"],
        access_token=token,
        send_allowlist=allowlist,
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
    )
