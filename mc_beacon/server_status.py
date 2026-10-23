"""服务器自建状态接口：读取主机指标并拼成纯文本段落。"""

import asyncio
import json

import aiohttp
from astrbot.api import logger

TIMEOUT = 5

# 接口字段增减时只改这张表就行
FIELD_LABELS = {
    "serverVersion": "服务端版本",
    "gameVersion": "游戏版本",
    "serverTime": "服务器时间",
    "cpuLoad": "CPU 负载",
    "memoryLoad": "内存占用",
    "diskSpace": "磁盘空间",
    "lastBackup": "上次备份时间",
    "loopCount": "循环计数",
    "checksum": "校验和",
}


async def fetch_status_api(api_url: str) -> dict | None:
    """请求状态接口；未配置地址或失败时返回 None，不影响主流程。"""
    if not api_url:
        return None

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
            async with session.get(api_url, headers={"User-Agent": "MCBeacon/0.3.1"}) as response:
                text = await response.text()
                if response.status != 200:
                    logger.warning(f"[server_status] HTTP错误: {response.status}, url={api_url}")
                    return None
                data = json.loads(text)
                if not isinstance(data, dict):
                    logger.warning(f"[server_status] 接口返回的不是 JSON 对象: {text[:200]}")
                    return None
                return data
    except asyncio.TimeoutError:
        logger.warning(f"[server_status] 请求超时（{TIMEOUT}s）: {api_url}")
    except Exception as exc:
        logger.warning(f"[server_status] 请求失败: {exc}, url={api_url}")
    return None


def format_status_section(data: dict | None) -> str:
    """只输出接口里确实有值的字段，全为空时返回空串。"""
    if not data:
        return ""

    lines: list[str] = []
    for key, label in FIELD_LABELS.items():
        value = data.get(key)
        if value is None or str(value).strip() == "":
            continue
        lines.append(f"  {label}: {str(value).strip()}")

    if not lines:
        return ""
    return "服务器状态\n" + "\n".join(lines)
