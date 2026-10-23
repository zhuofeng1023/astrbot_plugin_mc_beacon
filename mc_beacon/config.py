"""配置读取：把 WebUI 里的原始配置换成服务器列表。"""

import re

from astrbot.api import AstrBotConfig, logger

from .models import ServerConfig, ServerState


def safe_int(value, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def safe_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default

    value_str = str(value).strip().lower()
    if value_str in {"true", "1", "yes", "on"}:
        return True
    if value_str in {"false", "0", "no", "off"}:
        return False
    return default


def parse_target_group(value) -> str | None:
    """群号只接受纯数字，填了别的东西就当没填，避免发送时 int() 直接炸。"""
    if value is None:
        return None
    value = str(value).strip()
    return value if value.isdigit() else None


def normalize_server_type(server_type: str) -> str:
    normalized = str(server_type or "java").strip().lower()
    return normalized if normalized in {"bedrock", "java"} else "java"


def slugify_server_key(server_name: str, fallback: str) -> str:
    """中文名称生成不出可用标识，回退成 server_N。"""
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", server_name.strip().lower()).strip("_")
    return normalized or fallback


def resolve_check_interval(value, global_check_interval: int) -> int:
    interval = safe_int(value, global_check_interval)
    if interval <= 0:
        return global_check_interval
    return max(5, interval)


def load_servers_from_config(config: AstrBotConfig, global_check_interval: int) -> list[ServerConfig]:
    """读取 server_entries，跳过没填地址的条目。"""
    raw_servers = config.get("server_entries", [])
    if not isinstance(raw_servers, list):
        logger.warning("配置项 server_entries 不是列表，已忽略。")
        raw_servers = []

    servers: list[ServerConfig] = []
    for index, item in enumerate(raw_servers, start=1):
        if not isinstance(item, dict):
            logger.warning(f"server_entries 第 {index} 项不是对象，已跳过。")
            continue

        server_ip = str(item.get("server_ip", "")).strip()
        if not server_ip:
            logger.warning(f"server_entries 第 {index} 项缺少 server_ip，已跳过。")
            continue

        server_name = str(item.get("server_name", "")).strip() or server_ip
        servers.append(
            ServerConfig(
                key=slugify_server_key(server_name, f"server_{index}"),
                server_name=server_name,
                server_ip=server_ip,
                server_port=safe_int(item.get("server_port", 25565), 25565),
                server_type=normalize_server_type(item.get("server_type", "java")),
                check_interval=resolve_check_interval(
                    item.get("check_interval", global_check_interval), global_check_interval
                ),
                status_api_url=str(item.get("status_api_url", "") or "").strip(),
            )
        )

    if len({server.key for server in servers}) != len(servers):
        logger.warning("存在同名服务器，监控状态会共用，建议给服务器取不同名称。")

    return servers


def build_initial_states(servers: list[ServerConfig]) -> dict[str, ServerState]:
    return {server.key: ServerState() for server in servers}


# 展示开关默认值；键名与 _conf_schema.json 的 display.items 一致
DISPLAY_DEFAULTS = {
    "server_name": True,
    "status": True,
    "address": True,
    "server_type": True,
    "version": True,
    "motd": True,
    "update_time": True,
    "online_count": True,
    "player_list": True,
    "serverVersion": True,
    "gameVersion": True,
    "serverTime": True,
    "cpuLoad": True,
    "memoryLoad": True,
    "diskSpace": True,
    "lastBackup": True,
    "loopCount": True,
    "checksum": True,
}


def load_display_options(config: AstrBotConfig) -> dict[str, bool]:
    """读 display 分组；缺省或非法值一律按展示处理。"""
    raw = config.get("display", {})
    if not isinstance(raw, dict):
        raw = {}
    return {key: safe_bool(raw.get(key, default), default) for key, default in DISPLAY_DEFAULTS.items()}
