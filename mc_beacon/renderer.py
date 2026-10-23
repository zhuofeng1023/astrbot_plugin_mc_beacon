import pylitehtml
import os

def generate_dashboard_image():
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
        "cpuLoad": "35.5%",     # 带 % 号
        "memoryLoad": "68",     # 不带 % 号，模板内会自动处理
        "diskSpace": "82%",
        "lastBackup": "2023-10-26 03:00:00",
        # 故意不传 playerCount，测试模板降级到 snapshot.online
    }

    FIELD_LABELS = {
        "cpuLoad": "CPU 负载",
        "memoryLoad": "内存占用",
        "diskSpace": "磁盘空间",
        "lastBackup": "上次备份时间",
    }

    # 2. 获取模板绝对路径
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Template", "template.html")
    
    # 3. 使用 pylitehtml 渲染并生成 PNG 字节流
    # 核心特性：render_file 会自动识别 .html 文件中的 Jinja2 语法，
    # 并将后续的关键字参数 (snapshot=..., status_data=...) 作为模板变量注入。
    print("正在渲染图片...")
    png_bytes = pylitehtml.render_file(
        template_path,
        width=480,       # 手机APP标准宽度
        scale=2,         # HiDPI 2倍缩放，让文字和边框在图片中极其清晰锐利
        fmt="png",
        snapshot=snapshot_data,
        status_data=status_data_dict,
        FIELD_LABELS=FIELD_LABELS
    )

    # 4. 保存为本地图片文件
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Temp"), exist_ok=True)
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Temp/dashboard_output.png")
    with open(output_path, "wb") as f:
        f.write(png_bytes)
    
    print(f"✅ 渲染成功！图片已保存至: {output_path}")

if __name__ == "__main__":
    generate_dashboard_image()
