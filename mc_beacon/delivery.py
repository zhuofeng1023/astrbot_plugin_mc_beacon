"""群消息发送：只走 OneBot（AIOCQHTTP）适配器发纯文本。"""

import asyncio

from astrbot.api import logger
from astrbot.api.event.filter import PlatformAdapterType

READY_TIMEOUT = 12


async def _wait_for_client(context):
    """平台适配器通常比插件晚启动，等一下再取客户端，取不到就不发这条通知。"""
    adapter_type = getattr(PlatformAdapterType, "AIOCQHTTP", None)
    deadline = asyncio.get_running_loop().time() + READY_TIMEOUT
    while True:
        platform = context.get_platform(adapter_type) if adapter_type is not None else None
        client = platform.get_client() if hasattr(platform, "get_client") else None
        if client:
            return client

        if asyncio.get_running_loop().time() >= deadline:
            logger.error("无法获取可用的 OneBot 平台客户端，通知未发送")
            return None
        await asyncio.sleep(1)


async def notify_group(context, target_group: str | None, message: str) -> bool:
    if not target_group:
        logger.error("target_group 未配置，无法发送通知")
        return False

    client = await _wait_for_client(context)
    if client is None:
        return False

    try:
        result = await client.api.call_action(
            "send_group_msg",
            group_id=int(target_group),
            message=message,
        )
    except Exception as exc:
        logger.error(f"发送群消息异常: {exc}")
        return False

    if result and result.get("message_id"):
        logger.info(f"群消息发送成功，message_id={result.get('message_id')}")
        return True

    logger.warning(f"发送群消息失败: {result}")
    return False
