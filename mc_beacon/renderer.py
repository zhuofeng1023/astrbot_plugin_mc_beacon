import os

import pylitehtml


def generate_dashboard_image(snapshot_data, status_data=None, theme="dark", scale=3, display=None):
    """将服务器状态渲染为 PNG 字节流，不写入本地文件。"""
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Template", "template1.html")
    status_data = status_data or {}
    display = display or {}
    field_labels = {
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
    return pylitehtml.render_file(
        template_path,
        width=480 * scale,
        fmt="png",
        root_size=16 * scale,
        snapshot=snapshot_data,
        status_data=status_data,
        theme=theme,
        FIELD_LABELS=field_labels,
        display=display,
    )
