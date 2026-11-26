import hmac
import json
from typing import Any

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from telethon import utils
from telethon.tl.types import User

from app.config import load_settings
from app.telegram_client import get_telegram_client

mcp = FastMCP("Telegram-MCP", stateless_http=True)


def message_data(message: Any, sender: Any = None) -> dict[str, Any]:
    name = None
    if sender:
        name = " ".join(
            part for part in (getattr(sender, "first_name", None), getattr(sender, "last_name", None))
            if part
        ) or None
    return {
        "id": message.id,
        "date": message.date.isoformat() if message.date else None,
        "text": message.message or "",
        "sender_id": getattr(sender, "id", None),
        "sender_name": name,
        "reply_to_msg_id": getattr(message, "reply_to_msg_id", None),
        "has_media": bool(message.media),
        "outgoing": bool(message.out),
    }


async def serialize_messages(messages: list[Any]) -> list[dict[str, Any]]:
    client = await get_telegram_client()
    output = []
    for message in reversed(messages):
        if message:
            try:
                sender = await message.get_sender()
            except Exception:
                sender = None
            output.append(message_data(message, sender))
    return output


@mcp.tool()
async def get_dialogs(limit: int = 30) -> list[dict[str, Any]]:
    """List recent Telegram dialogs. Limit is clamped to 1..100."""
    client = await get_telegram_client()
    output = []
    async for dialog in client.iter_dialogs(limit=max(1, min(limit, 100))):
        output.append({
            "id": utils.get_peer_id(dialog.entity),
            "name": dialog.name,
            "is_user": bool(dialog.is_user),
            "is_group": bool(dialog.is_group),
            "is_channel": bool(dialog.is_channel),
            "unread_count": dialog.unread_count,
            "last_message_date": (
                dialog.message.date.isoformat()
                if dialog.message and dialog.message.date else None
            ),
        })
    return output


@mcp.tool()
async def get_contacts(limit: int = 100) -> list[dict[str, Any]]:
    """List saved Telegram contacts, up to 200."""
    client = await get_telegram_client()
    contacts = await client.get_contacts()
    return [
        {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "phone": user.phone,
            "is_bot": user.bot,
        }
        for user in contacts[:max(1, min(limit, 200))]
    ]


@mcp.tool()
async def get_messages(chat_id: int, limit: int = 30) -> list[dict[str, Any]]:
    """Read recent messages from a dialog by numeric Telegram peer ID."""
    client = await get_telegram_client()
    entity = await client.get_entity(chat_id)
    messages = await client.get_messages(entity, limit=max(1, min(limit, 100)))
    return await serialize_messages(list(messages))


@mcp.tool()
async def search_messages(chat_id: int, query: str, limit: int = 30) -> list[dict[str, Any]]:
    """Search text within one dialog by numeric peer ID."""
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")
    client = await get_telegram_client()
    entity = await client.get_entity(chat_id)
    messages = await client.get_messages(
        entity, search=query.strip()[:200], limit=max(1, min(limit, 100))
    )
    return await serialize_messages(list(messages))


@mcp.tool()
async def get_user_info(user_id: int) -> dict[str, Any]:
    """Get basic Telegram profile information for a user by numeric ID."""
    client = await get_telegram_client()
    entity = await client.get_entity(user_id)
    if not isinstance(entity, User):
        raise ValueError("The supplied ID does not resolve to a Telegram user")
    return {
        "id": entity.id,
        "first_name": entity.first_name,
        "last_name": entity.last_name,
        "username": entity.username,
        "phone": entity.phone,
        "is_bot": entity.bot,
        "is_verified": entity.verified,
        "is_premium": entity.premium,
    }


@mcp.tool()
async def send_message(chat_id: int, text: str, confirm: bool = False) -> dict[str, Any]:
    """Send only if confirm=true and chat_id is in the configured numeric allowlist."""
    if confirm is not True:
        raise ValueError("Sending requires explicit confirm=true")
    if not text or not text.strip():
        raise ValueError("Message text cannot be empty")
    if len(text) > 4096:
        raise ValueError("Message exceeds Telegram's 4096-character limit")

    settings = load_settings()
    if chat_id not in settings.send_allowlist:
        raise PermissionError(
            "Destination is not allowlisted. Add its verified numeric peer ID "
            "to TELEGRAM_SEND_ALLOWLIST in the host settings."
        )

    client = await get_telegram_client()
    entity = await client.get_entity(chat_id)
    sent = await client.send_message(entity, text.strip(), link_preview=False)
    return {
        "sent": True,
        "chat_id": chat_id,
        "message_id": sent.id,
        "date": sent.date.isoformat() if sent.date else None,
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "Telegram-MCP"})


@mcp.custom_route("/", methods=["GET"])
async def root(_: Request) -> JSONResponse:
    return JSONResponse({"service": "Telegram-MCP", "mcp_endpoint": "/mcp", "health": "/health"})


class BearerAuthASGI:
    """Require a bearer token for MCP HTTP requests."""

    def __init__(self, app, token: str):
        self.app = app
        self.expected = ("Bearer " + token).encode("utf-8")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").startswith("/mcp"):
            headers = dict(scope.get("headers", []))
            supplied = headers.get(b"authorization", b"")
            if not hmac.compare_digest(supplied, self.expected):
                body = json.dumps({"error": "Unauthorized"}).encode("utf-8")
                await send({
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                })
                await send({"type": "http.response.body", "body": body})
                return
        await self.app(scope, receive, send)


# Load settings at startup/import time so misconfiguration fails early.
settings = load_settings()
app = BearerAuthASGI(mcp.streamable_http_app(), settings.access_token)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
