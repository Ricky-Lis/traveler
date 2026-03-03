"""
逆地理编码：高德 Web 服务 API
文档: https://lbs.amap.com/api/webservice/guide/api/georegeo
"""
import httpx

from app.config import get_settings

REGRO_URL = "https://restapi.amap.com/v3/geocode/regeo"


def reverse_geocode(lng: float, lat: float) -> dict | None:
    """
    逆地理编码：经纬度 -> 地址信息（同步，供 asyncio.to_thread 调用）。
    若未配置 AMAP_WEB_SERVICE_KEY 或请求失败，返回 None。
    返回字段: location_name, address, district, city_name, province_name, country_name
    """
    settings = get_settings()
    if not settings.AMAP_WEB_SERVICE_KEY:
        return None

    location = f"{lng},{lat}"
    params = {
        "key": settings.AMAP_WEB_SERVICE_KEY,
        "location": location,
        "output": "json",
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(REGRO_URL, params=params)
            data = resp.json()
    except Exception:
        return None

    if str(data.get("status")) != "1":
        return None

    regeocode = data.get("regeocode") or {}
    address_component = regeocode.get("addressComponent") or {}
    formatted = regeocode.get("formatted_address") or ""

    # 最近 POI 作为 location_name（可选）；无则用 formatted_address 首段或空
    pois = regeocode.get("pois") or []
    location_name = ""
    if pois and isinstance(pois, list) and len(pois) > 0:
        first = pois[0]
        if isinstance(first, dict):
            location_name = first.get("name") or ""
    if not location_name:
        location_name = formatted.split()[0] if formatted else ""

    return {
        "location_name": location_name[:255],
        "address": (formatted or "")[:500],
        "district": (address_component.get("district") or "")[:100],
        "city_name": (address_component.get("city") or address_component.get("province") or "")[:100],
        "province_name": (address_component.get("province") or "")[:100],
        "country_name": (address_component.get("country") or "中国")[:100],
    }
