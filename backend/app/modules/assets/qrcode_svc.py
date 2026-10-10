"""资产二维码：生成带签名的溯源令牌、渲染可打印贴纸、扫码验签解析。

二维码内容是一个「签名令牌」，而非裸资产 id：即使有人仿造二维码，也过不了
服务端签名校验，从而实现一物一码的防伪与溯源。
"""

import base64
from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M

from app.core.sign import sign, verify
from app.modules.assets.models import Asset
from app.modules.meta import service as meta_service
from app.modules.org.models import OrgUnit

_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhl.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def _font(size: int):
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def build_token(asset: Asset) -> str:
    """生成二维码令牌：base64(载荷) + HMAC 签名，防伪造。"""
    payload = f"{asset.id}|{asset.code}|{asset.org_unit_id or 0}"
    b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{b64}.{sign(payload)}"


def parse_token(token: str) -> tuple[int, str, int] | None:
    """解析并验签；失败返回 None。返回 (asset_id, code, org_unit_id)。"""
    try:
        b64, sig = token.split(".", 1)
        payload = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4)).decode("utf-8")
        if not verify(payload, sig):
            return None
        asset_id, code, org_id = payload.split("|")
        return int(asset_id), code, int(org_id)
    except Exception:
        return None


def root_org_name(db, org_unit_id: int | None) -> str:
    """向上回溯到园区（幼儿园）层级名称；无组织归属时返回空串。"""
    unit = db.get(OrgUnit, org_unit_id) if org_unit_id else None
    if not unit:
        return ""
    seen: set[int] = set()
    while unit.parent_id and unit.id not in seen:
        seen.add(unit.id)
        parent = db.get(OrgUnit, unit.parent_id)
        if parent is None:
            break
        unit = parent
    return unit.name


def build_info_text(asset: Asset, org_name: str) -> str:
    """二维码内容：直接承载可读的资产信息，扫码即可查看，无需联网。"""
    lines = [org_name or "—"]
    lines.append(f"资产：{asset.name}")
    lines.append(f"编号：{asset.code}")
    if asset.location:
        lines.append(f"位置：{asset.location}")
    lines.append(f"数量：{asset.quantity}{asset.unit or ''}")
    lines.append(f"状态：{meta_service.asset_status_text(asset.status)}")
    return "\n".join(lines)


def render_sticker(asset: Asset, org_name: str, qr_text: str) -> bytes:
    """渲染一张资产贴纸 PNG（二维码内容为资产信息），可直接打印。"""
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=8, border=1)
    qr.add_data(qr_text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f2723", back_color="white").convert("RGB").resize((236, 236))

    width, height = 340, 452
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, 44], fill="#0e6b5c")
    draw.text((16, 12), "园小助 · 资产标签", font=_font(17), fill="white")
    img.paste(qr_img, ((width - 236) // 2, 60))

    y = 316
    draw.text((18, y), asset.code, font=_font(19), fill="#123b34")
    y += 28
    name = asset.name if len(asset.name) <= 15 else asset.name[:15] + "…"
    draw.text((18, y), name, font=_font(15), fill="#23302c")
    y += 26
    draw.text((18, y), f"归属：{org_name or '—'}", font=_font(13), fill="#6b6355")
    y += 22
    draw.text((18, y), f"位置：{asset.location or '—'}", font=_font(13), fill="#6b6355")
    draw.text((18, height - 24), "扫码查看资产信息", font=_font(11), fill="#a9a396")

    bio = BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def scan_card(db, token: str) -> dict:
    """扫码解析（公开只读）：验签后仅返回非敏感字段。"""
    parsed = parse_token(token)
    if not parsed:
        return {"valid": False, "message": "二维码无效或已被篡改（签名校验未通过）。"}
    asset_id, code, _ = parsed
    asset = db.get(Asset, asset_id)
    if not asset or asset.code != code:
        return {"valid": False, "message": "未找到对应资产，可能已被删除。"}
    org = db.get(OrgUnit, asset.org_unit_id) if asset.org_unit_id else None
    return {
        "valid": True,
        "id": asset.id,
        "name": asset.name,
        "code": asset.code,
        "status": asset.status,
        "status_text": meta_service.asset_status_text(asset.status),
        "status_tone": meta_service.asset_status_tone(asset.status),
        "category": asset.category.name if asset.category else "未分类",
        "org_name": org.name if org else "—",
        "location": asset.location or "—",
        "quantity": asset.quantity,
        "unit": asset.unit,
        "safety_level": asset.safety_level or "—",
        "age_range": asset.age_range or "—",
        "message": "签名校验通过，资产信息真实有效。",
    }
