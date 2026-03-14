import json
from urllib import error, request

from fastapi import HTTPException, status

from backend.models import NotificationSetting


def build_webhook_payload(channel: str, text: str) -> dict:
    if channel == "wecom":
        return {"msgtype": "text", "text": {"content": text}}
    if channel == "feishu":
        return {"msg_type": "text", "content": {"text": text}}
    return {"text": text}


def send_webhook_message(setting: NotificationSetting, text: str) -> None:
    webhook_url = setting.webhook_url.strip()
    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification webhook URL is not configured",
        )

    payload = build_webhook_payload(setting.channel, text)
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Notification webhook request failed",
                )
    except HTTPException:
        raise
    except error.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Notification webhook request failed: {exc.code}",
        ) from exc
    except error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Notification webhook is unreachable",
        ) from exc


def build_prefixed_text(setting: NotificationSetting, text: str) -> str:
    prefix = setting.message_prefix.strip()
    if not prefix:
        return text
    return f"[{prefix}] {text}"
