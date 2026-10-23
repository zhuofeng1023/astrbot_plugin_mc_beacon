"""公开查询源：走 MineBBS 的 MOTD 接口拿服务器状态。"""

import asyncio
from datetime import datetime

import aiohttp
from astrbot.api import logger

from .models import ServerConfig, ServerSnapshot

API_URL = "https://motd.minebbs.com/api/status"
TIMEOUT = 15


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_player_names(player_list) -> list[str]:
    if not isinstance(player_list, list):
        return []

    names: list[str] = []
    for player in player_list:
        if isinstance(player, dict):
            names.append(str(player.get("name_clean") or player.get("name") or player.get("username") or "未知玩家"))
        else:
            names.append(str(player))
    return names


def _parse_response(server: ServerConfig, data: dict) -> ServerSnapshot:
    online = str(data.get("status", "offline")).strip().lower() == "online"

    raw_type = str(data.get("type", "")).strip().lower()
    server_type = raw_type if raw_type in {"java", "bedrock"} else server.server_type

    players_info = data.get("players", {})
    if isinstance(players_info, dict):
        online_players = int(players_info.get("online", 0) or 0)
        max_players = int(players_info.get("max", 0) or 0)
        player_names = _normalize_player_names(players_info.get("sample", []))
    else:
        online_players = 0
        max_players = 0
        player_names = []

    motd_info = data.get("motd", {})
    if isinstance(motd_info, dict):
        motd = str(data.get("pureMotd") or motd_info.get("text") or "")
    else:
        motd = str(data.get("pureMotd") or motd_info or "")

    return ServerSnapshot(
        key=server.key,
        name=server.server_name,
        server_ip=server.server_ip,
        server_port=server.server_port,
        server_type=server_type,
        status="online" if online else "offline",
        motd=motd,
        version=str(data.get("version", "未知版本")),
        online=online_players,
        max_players=max_players,
        players=player_names,
        update_time=_now_text(),
    )


async def fetch_status(server: ServerConfig, source: str) -> ServerSnapshot | None:
    """查询一台服务器；任何异常都只记日志并返回 None，让监控循环继续跑下一台。"""
    params = {
        "ip": server.server_ip,
        "port": str(server.server_port),
        # MineBBS 用 je/be 区分 Java 与基岩版
        "stype": "je" if server.server_type == "java" else "be",
        "_ts": str(int(datetime.now().timestamp() * 1000)),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                API_URL,
                params=params,
                headers={"User-Agent": "MCBeacon/0.3.1", "Cache-Control": "no-cache"},
                timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            ) as response:
                raw_text = await response.text()
                if response.status != 200:
                    logger.warning(
                        f"[{source}] [{server.server_name}] MineBBS HTTP错误: "
                        f"{response.status}, body={raw_text[:300]}"
                    )
                    return None
                data = await response.json(content_type=None)
                return _parse_response(server, data)
    except asyncio.TimeoutError:
        logger.warning(f"[{source}] [{server.server_name}] MineBBS 查询超时")
        return None
    except aiohttp.ClientError as exc:
        logger.warning(f"[{source}] [{server.server_name}] MineBBS 网络错误: {exc}")
        return None
    except Exception as exc:
        logger.error(f"[{source}] [{server.server_name}] MineBBS 查询异常: {exc}")
        return None
