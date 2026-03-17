import re

from fastapi import HTTPException, status

HIGH_RISK_PATTERNS = [
    "加微信",
    "加v",
    "加V",
    "私聊",
    "私信下单",
    "扫码进群",
    "领券加群",
    "返利",
    "刷单",
    "赌博",
    "色情",
]
HIGH_RISK_REGEXES = [
    re.compile(r"微\s*信"),
    re.compile(r"v\s*信", re.IGNORECASE),
    re.compile(r"vx", re.IGNORECASE),
]

CONTACT_GUIDANCE_PATTERNS = [
    "私下交易",
    "扫码加群",
    "加微信下单",
    "加微信领券",
    "私聊获取",
]


def ensure_safe_text(value: str, *, field_label: str) -> str:
    normalized = value.strip()
    if not normalized:
        return normalized

    lowered = normalized.lower()
    for keyword in HIGH_RISK_PATTERNS:
        if keyword.lower() in lowered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_label}包含高风险内容，请修改后再提交",
            )

    for pattern in HIGH_RISK_REGEXES:
        if pattern.search(normalized):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_label}包含高风险内容，请修改后再提交",
            )

    return normalized


def ensure_compliant_storefront_text(value: str, *, field_label: str) -> str:
    normalized = value.strip()
    if not normalized:
        return normalized

    lowered = normalized.lower()
    for keyword in CONTACT_GUIDANCE_PATTERNS:
        if keyword.lower() in lowered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_label}包含导流风险文案，请改为电话、地址或营业时间等必要信息",
            )

    return normalized
