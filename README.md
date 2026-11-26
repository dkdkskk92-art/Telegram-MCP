# Telegram-MCP

A self-hosted MCP server for your own Telegram user account, using Telethon.

## Included tools

- `get_dialogs`: list recent chats.
- `get_contacts`: list saved contacts.
- `get_messages`: read recent messages from one dialog.
- `search_messages`: search within one dialog.
- `get_user_info`: retrieve basic user profile details.
- `send_message`: requires explicit `confirm=true` and a numeric destination ID in `TELEGRAM_SEND_ALLOWLIST`.

The HTTP MCP endpoint is protected by a bearer token. The Telegram session is supplied only through host secrets and is never committed.

## Security

- Keep this repository **Private**.
- Never commit or share `TELEGRAM_SESSION`, API credentials, `.session` files, login codes, or 2FA passwords.
- Generate the Telethon StringSession on your own trusted computer and paste it directly into Bothost's secret settings.
- Keep `TELEGRAM_SEND_ALLOWLIST` empty until you have verified the numeric peer IDs you intend to message.
- Secret Chats are not supported.
- This is a user-account client; use only your own account and comply with Telegram's terms.

## Environment variables

| Name | Required | Description |
|---|---:|---|
| `TELEGRAM_API_ID` | yes | API ID from https://my.telegram.org |
| `TELEGRAM_API_HASH` | yes | API hash from https://my.telegram.org |
| `TELEGRAM_SESSION` | yes | Telethon StringSession (host secret only) |
| `MCP_ACCESS_TOKEN` | yes | Random bearer token, at least 32 characters |
| `TELEGRAM_SEND_ALLOWLIST` | no | Comma-separated numeric Telegram peer IDs; empty disables sending |
| `HOST` | no | Defaults to `0.0.0.0` |
| `PORT` | no | Defaults to `8000` |

## Create the session locally

Install dependencies, then run the helper from a trusted computer:

```bash
python -m venv .venv
# activate the virtual environment
pip install -r requirements.txt
TELEGRAM_API_ID=YOUR_ID TELEGRAM_API_HASH=YOUR_HASH python scripts/create_session.py
```

The helper prompts for your phone number and Telegram login code in the local terminal. It prints a StringSession once. Copy it directly into Bothost's `TELEGRAM_SESSION` secret. Do not paste it into ChatGPT or GitHub.

## Run

```bash
uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8000}
```

- MCP Streamable HTTP endpoint: `/mcp`
- Health endpoint: `/health` (does not expose credentials or Telegram data)
- MCP authorization header: `Authorization: Bearer <MCP_ACCESS_TOKEN>`

## Bothost

Create a separate Python web application connected to this repository. Add the environment variables as secrets in Bothost and use this start command:

```bash
uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8000}
```

Do not upload a session file to GitHub. Verify the host's persistent storage and secret settings before deployment.

This is an initial scaffold; test read-only tools first. Sending remains disabled until an explicit numeric allowlist is configured.
