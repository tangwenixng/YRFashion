import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from backend.core.config import settings

WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


class MiniappAuthConfigurationError(RuntimeError):
    pass


class MiniappAuthExchangeError(RuntimeError):
    pass


@dataclass(slots=True)
class MiniappCode2SessionResult:
    openid: str
    unionid: str | None = None


def resolve_miniapp_session_from_code(code: str) -> MiniappCode2SessionResult:
    app_id = settings.miniapp_app_id.strip()
    app_secret = settings.miniapp_app_secret.strip()
    if not app_id or not app_secret:
        raise MiniappAuthConfigurationError("未配置小程序登录凭证")

    query = urlencode(
        {
            "appid": app_id,
            "secret": app_secret,
            "js_code": code.strip(),
            "grant_type": "authorization_code",
        }
    )

    try:
        with urlopen(f"{WECHAT_CODE2SESSION_URL}?{query}", timeout=8) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise MiniappAuthExchangeError("微信登录服务返回异常，请稍后重试") from error
    except URLError as error:
        raise MiniappAuthExchangeError("微信登录服务请求失败，请稍后重试") from error
    except json.JSONDecodeError as error:
        raise MiniappAuthExchangeError("微信登录服务返回了无法解析的数据") from error

    errcode = payload.get("errcode")
    if errcode:
        errmsg = str(payload.get("errmsg") or "未知错误")
        raise MiniappAuthExchangeError(f"微信登录失败：{errmsg}（{errcode}）")

    openid = str(payload.get("openid") or "").strip()
    if not openid:
        raise MiniappAuthExchangeError("微信登录返回缺少 openid")

    unionid = str(payload.get("unionid") or "").strip() or None
    return MiniappCode2SessionResult(openid=openid, unionid=unionid)
