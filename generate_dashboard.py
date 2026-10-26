import os
from pathlib import Path
import pylitehtml


def generate_dashboard_image(theme="dark"):
    """
    theme: "dark"（暗色）或 "light"（亮色）
    其余 snapshot/status_data 字段可按现有数据源传入，不需要改变字段结构。
    """
    theme = str(theme).lower().strip()
    if theme not in ("dark", "light"):
        raise ValueError("theme 只支持 'dark' 或 'light'")

    # 示例数据：接入实际数据时，保留原有字典字段即可
    snapshot_data = {
        "name": "我的世界-周末生存服",
        "server_ip": "play.myserver.com",
        "server_port": 25565,
        "server_type": "Paper",
        "status": "online",
        "motd": "欢迎来到本服！\n本周六晚8点有抽奖活动",
        "version": "1.20.1",
        "online": 3,
        "max_players": 20,
        "players": ["Steve", "Alex", "Herobrine"],
        "update_time": "2023-10-27 18:30:00",
    }

    status_data_dict = {
        "serverVersion": "Paper 1.20.1-b123",
        "cpuLoad": "35.5%",
        "memoryLoad": "68",
        "diskSpace": "82%",
        "lastBackup": "2023-10-26 03:00:00",
    }

    template_path = Path(__file__).resolve().parent / "mc_beacon" / "Template" / "template1.html"
    output_dir = Path(__file__).resolve().parent / "Temp"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"dashboard_{theme}.png"

    print(f"正在渲染图片（{theme} 主题）...")
    png_bytes = pylitehtml.render_file(
        str(template_path),
        width=960,      # 480 * 2，视口随缩放等比放大
        root_size=32,   # 等比放大 2 倍（1rem=设计稿16px，root_size=16*2）
        fmt="png",
        snapshot=snapshot_data,
        status_data=status_data_dict,
        theme=theme,  # 只需改这个参数即可切换暗色/亮色
    )

    output_path.write_bytes(png_bytes)
    print(f"渲染成功！图片已保存至: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    generate_dashboard_image(theme="dark")   # 暗色主题
    # generate_dashboard_image(theme="light")  # 亮色主题
