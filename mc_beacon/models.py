from dataclasses import dataclass, field


@dataclass(slots=True)
class ServerConfig:
    """配置页里的一条服务器配置，key 由名称生成，用于内部索引状态。"""

    key: str
    server_name: str
    server_ip: str
    server_port: int
    server_type: str
    check_interval: int
    status_api_url: str = ""


@dataclass(slots=True)
class ServerState:
    """上一轮巡检留下的记忆，用来判断这一轮有没有变化。"""

    last_player_count: int | None = None
    last_player_list: list[str] = field(default_factory=list)
    last_status: str | None = None
    last_check_ts: float = 0.0


@dataclass(slots=True)
class ServerSnapshot:
    """一次公开查询拿到的服务器状态快照。"""

    key: str
    name: str
    server_ip: str
    server_port: int
    server_type: str
    status: str
    motd: str
    version: str
    online: int
    max_players: int
    players: list[str]
    update_time: str
