import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

from app.config import load_settings

_client: TelegramClient | None = None
_lock = asyncio.Lock()


async def get_telegram_client() -> TelegramClient:
    global _client
    if _client is not None and _client.is_connected():
        return _client

    async with _lock:
        if _client is not None and _client.is_connected():
            return _client

        settings = load_settings()
        client = TelegramClient(
            StringSession(settings.session),
            settings.api_id,
            settings.api_hash,
            request_retries=2,
            connection_retries=3,
            auto_reconnect=True,
        )
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            raise RuntimeError(
                "Telegram session is not authorized. Generate a new StringSession locally "
                "and replace the TELEGRAM_SESSION secret in Bothost."
            )
        _client = client
        return client
