"""插件入口：读取配置、跑监控循环、提供 /查询 指令，状态变化时发纯文本群通知。"""

import asyncio
import os
import sys

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if PLUGIN_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_DIR)

from mc_beacon.clients import fetch_status
from mc_beacon.config import (
    build_initial_states,
    load_servers_from_config,
    parse_target_group,
    safe_bool,
    safe_int,
)
from mc_beacon.delivery import notify_group
from mc_beacon.models import ServerConfig, ServerSnapshot, ServerState
from mc_beacon.monitor import compose_server_block, detect_changes
from mc_beacon.server_status import fetch_status_api

__all__ = ["MCBeaconPlugin"]


@register("mc_beacon", "zhuofeng", "MC 服务器监控", "0.3.1")
class MCBeaconPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        config = config or {}

        self.target_group = parse_target_group(config.get("target_group"))
        self.global_check_interval = max(5, safe_int(config.get("check_interval", 45), 45))
        self.servers = load_servers_from_config(config, self.global_check_interval)
        self.server_states = build_initial_states(self.servers)
        self.server_locks = {server.key: asyncio.Lock() for server in self.servers}
        self.task: asyncio.Task | None = None

        logger.info(
            f"MC 服务器监控已加载，目标群: {self.target_group}, "
            f"服务器数: {len(self.servers)}, 默认检测间隔: {self.global_check_interval}s"
        )

        if safe_bool(config.get("enable_auto_monitor", True), True) and self.servers:
            self.task = asyncio.create_task(self.monitor_loop())

    async def terminate(self):
        """插件卸载/重载时收掉监控循环，别留孤儿任务。"""
        if self.task and not self.task.done():
            self.task.cancel()
            logger.info("服务器监控任务已停止")

    async def _fetch_server(self, server: ServerConfig, source: str) -> ServerSnapshot | None:
        """同一台服务器同时只允许一个查询在飞，避免手动查询和监控循环互相干扰。"""
        lock = self.server_locks.setdefault(server.key, asyncio.Lock())
        async with lock:
            return await fetch_status(server, source=source)

    async def _server_detail(self, server: ServerConfig, snapshot: ServerSnapshot | None) -> str:
        """拼装纯文本详情：已有查询结果 + 自建状态接口（未配置就跳过）。"""
        status_data = await fetch_status_api(server.status_api_url)
        return compose_server_block(snapshot, status_data)

    async def monitor_loop(self):
        try:
            while True:
                await asyncio.sleep(1)
                now = asyncio.get_running_loop().time()

                for server in self.servers:
                    state = self.server_states.setdefault(server.key, ServerState())
                    if now - state.last_check_ts < server.check_interval:
                        continue

                    state.last_check_ts = now
                    snapshot = await self._fetch_server(server, "monitor")
                    if snapshot is None:
                        logger.warning(f"[monitor] [{server.server_name}] 本次未获取到服务器状态")
                        continue

                    changed, message = detect_changes(server, state, snapshot)
                    if not changed or not message:
                        continue

                    logger.info(f"[monitor] [{server.server_name}] 检测到状态变化: {message}")
                    detail = await self._server_detail(server, snapshot)
                    final_message = f"服务器状态变化\n{message}\n\n当前状态\n{detail}"
                    if not await notify_group(self.context, self.target_group, final_message):
                        logger.error(f"[monitor] [{server.server_name}] 状态变化已识别，但群消息发送失败")
        except asyncio.CancelledError:
            logger.info("监控循环已取消")
            raise
        except Exception as exc:
            logger.error(f"监控循环异常: {exc}")

    @filter.command("查询")
    async def query_server_status(self, event: AstrMessageEvent):
        """立即查询所有已配置服务器，纯文本返回。"""
        if not self.servers:
            yield event.plain_result("当前没有配置服务器，请先在 WebUI 中填写 server_entries")
            return

        blocks = []
        for index, server in enumerate(self.servers, start=1):
            snapshot = await self._fetch_server(server, "manual")
            detail = await self._server_detail(server, snapshot)
            blocks.append(f"===== {index}. {server.server_name} =====\n{detail}")
        yield event.plain_result("\n\n".join(blocks))
