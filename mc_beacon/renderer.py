import pylitehtml
import os

def generate_dashboard_image(theme, scale=3):
    # 1. 准备模拟数据 (字典格式，可残缺)
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
        "update_time": "2023-10-27 18:30:00"
    }

    status_data_dict = {
        "serverVersion": "Paper 1.20.1-b123",
        "gameVersion": "1.20.1",
        "serverTime": "2023-10-27 18:29:55",
        "cpuLoad": "35.5%",     # 带 % 号
        "memoryLoad": "68",     # 不带 % 号，模板内会自动处理
        "diskSpace": "82%",
        "lastBackup": "2023-10-26 03:00:00",
        "loopCount": 1024,
        "checksum": "a3f9c2e1",
        # playerCount / playerNames 与 snapshot 不同，用于验证「以 status 接口为准」
        "playerCount": 5,
        "playerNames": ["Steve", "Alex", "Herobrine", "Notch", "Jeb"],
    }

    # 显示开关：与 _conf_schema.json 的 display.items / config.DISPLAY_DEFAULTS 一致
    display_dict = {
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

    # 2. 获取模板绝对路径
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Template", "template1.html")
    
    # 3. 使用 pylitehtml 渲染并生成 PNG 字节流
    # 核心特性：render_file 会自动识别 .html 文件中的 Jinja2 语法，
    # 并将后续的关键字参数 (snapshot=..., status_data=...) 作为模板变量注入。
    print("正在渲染图片...")
    png_bytes = pylitehtml.render_file(
        template_path,
        width=480 * scale,  # 布局视口宽度随 scale 等比放大，保持设计图比例不变形
        fmt="png",
        # 等比缩放：模板内所有尺寸为 rem，root_size = 16 * scale 即整图放大 scale 倍
        # （scale=3 → 根字号 48px，输出像素宽 1440）
        root_size=16 * scale,
        snapshot=snapshot_data,
        status_data=status_data_dict,
        theme=theme,
        FIELD_LABELS=FIELD_LABELS,
        display=display_dict
    )

    # 4. 保存为本地图片文件
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Temp"), exist_ok=True)
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Temp/dashboard_output.png")
    with open(output_path, "wb") as f:
        f.write(png_bytes)
    
    print(f"✅ 渲染成功！图片已保存至: {output_path}")

if __name__ == "__main__":
    # generate_dashboard_image(theme="dark")   # 暗色主题
    generate_dashboard_image(theme="light", scale=3)  # 亮色主题，等比例放大 3 倍（输出 1440px 宽）
