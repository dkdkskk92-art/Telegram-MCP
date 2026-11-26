"""Create a Telethon StringSession locally. Never upload or share the output."""
import asyncio
import os

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in your local environment.")

    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.start()
    print("\nTelegram authorization succeeded.")
    print("Copy the following StringSession directly into Bothost's TELEGRAM_SESSION secret.")
    print("Do not paste it into ChatGPT, GitHub, or share it: it grants account access.\n")
    print(client.session.save())
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
