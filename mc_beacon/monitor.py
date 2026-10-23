"""纯文本展示组装与状态变化检测。"""

from .models import ServerConfig, ServerSnapshot, ServerState
from .server_status import format_status_section


def _format_basic_info(snapshot: ServerSnapshot) -> str:
    """基础信息段：名称、在线状态、地址、类型、版本、MOTD、更新时间。"""
    lines = [
        f"服务器: {snapshot.name}",
        f"状态: {'在线' if snapshot.status == 'online' else '离线'}",
        f"地址: {snapshot.server_ip}:{snapshot.server_port}",
        f"类型: {'基岩版' if snapshot.server_type == 'bedrock' else 'Java版'}",
        f"版本: {snapshot.version}",
    ]

    motd = snapshot.motd.strip()
    if motd:
        lines.append(f"MOTD: {motd[:120]}{'...' if len(motd) > 120 else ''}")

    lines.append(f"更新时间: {snapshot.update_time}")
    return "\n".join(lines)


def _format_player_section(snapshot: ServerSnapshot) -> str:
    """在线玩家段：人数与名单，名单为空时明确写出无人在线。"""
    count = f"{snapshot.online}/{snapshot.max_players}" if snapshot.max_players > 0 else str(snapshot.online)
    names = ", ".join(snapshot.players) if snapshot.players else "无人在线"
    return f"在线玩家\n  在线人数: {count}\n  玩家名单: {names}"


def compose_server_block(snapshot: ServerSnapshot | None, status_data: dict | None) -> str:
    """按「基础信息 -> 服务器状态 -> 在线玩家」拼出一台服务器的文本块。"""
    if snapshot is None:
        return "获取服务器数据失败"

    parts = [_format_basic_info(snapshot), format_status_section(status_data), _format_player_section(snapshot)]
    return "\n\n".join(part for part in parts if part)


def detect_changes(
    server: ServerConfig,
    state: ServerState,
    snapshot: ServerSnapshot,
) -> tuple[bool, str | None]:
    """对比上一轮快照，返回（是否变化, 变化描述）；同时把本轮结果写回 state。"""
    current_status = snapshot.status
    current_count = snapshot.online
    current_names = snapshot.players[:]

    # 第一轮没有可比的历史，只播报当前在线情况，避免上线就报“变化”
    if state.last_player_count is None:
        state.last_player_count = current_count
        state.last_player_list = current_names
        state.last_status = current_status
        if current_count > 0:
            return True, f"{server.server_name} 监控已启动，当前有玩家在线"
        return True, f"{server.server_name} 监控已启动"

    changes: list[str] = []

    if state.last_status != current_status:
        if current_status == "online":
            changes.append(f"{server.server_name} 已上线")
        else:
            changes.append(f"{server.server_name} 已离线")

    diff = current_count - state.last_player_count
    if diff > 0:
        new_players = sorted(set(current_names) - set(state.last_player_list))
        if new_players:
            changes.append(f"{server.server_name}: {', '.join(new_players)} 加入了服务器 (+{diff})")
        else:
            changes.append(f"{server.server_name}: 有 {diff} 名玩家加入了服务器")
    elif diff < 0:
        left_players = sorted(set(state.last_player_list) - set(current_names))
        if left_players:
            changes.append(f"{server.server_name}: {', '.join(left_players)} 离开了服务器 (-{abs(diff)})")
        else:
            changes.append(f"{server.server_name}: 有 {abs(diff)} 名玩家离开了服务器")

    state.last_player_count = current_count
    state.last_player_list = current_names
    state.last_status = current_status

    if changes:
        return True, "\n".join(changes)
    return False, None


__all__ = ["compose_server_block", "detect_changes"]
