import asyncio
import re
import requests
import websockets
import json

# -----------------------------
# 1. 提交测试任务
# -----------------------------
url = 'https://www.itdog.cn/http/'

form_data = {
    'line': '1,2,3',
    'host': 'fuckingfangbinxing.gateway-139.workers.dev',
    'host_s': 'fuckingfangbinxing.gateway-139.workers.dev',
    'check_mode': 'fast',
    'ipv4': 'www.shopify.com',   # 指定解析域名
    'method': 'get',
    'referer': '',
    'ua': '',
    'cookies': '',
    'redirect_num': '5',
    'dns_server_type': 'custom',
    'dns_server': '223.5.5.5'
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

resp = requests.post(url, data=form_data, headers=headers)
html_content = resp.text

# -----------------------------
# 2. 提取 task_id
# -----------------------------
# 从返回 HTML 中提取 task_id
task_id_match = re.search(r"var task_id='([0-9a-z]+)';", html_content)
if not task_id_match:
    raise ValueError("未找到 task_id")
task_id = task_id_match.group(1)
print("task_id:", task_id)

# -----------------------------
# 3. 建立 WebSocket 连接并接收测试结果
# -----------------------------
async def ws_test(task_id):
    wss_url = 'wss://www.itdog.cn/websockets'
    async with websockets.connect(wss_url) as ws:
        # 发送订阅消息（参考 JS create_websocket 内逻辑）
        subscribe_msg = json.dumps({
            "task_id": task_id
        })
        await ws.send(subscribe_msg)

        print("等待测试结果...")
        async for message in ws:
            data = json.loads(message)
            if data.get("type") == "success":
                # 输出节点测试结果
                print(f"Node: {data['name']}, IP: {data['ip']}, HTTP: {data['http_code']}, Time: {data['all_time']}s")
            elif data.get("type") == "finished":
                print("测试完成！")
                break

# -----------------------------
# 4. 运行 WS 事件循环
# -----------------------------
asyncio.get_event_loop().run_until_complete(ws_test(task_id))
