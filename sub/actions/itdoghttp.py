import asyncio
import re
import json
import aiohttp

# -----------------------------
# 1. 提交测试任务
# -----------------------------
print("测试开始！")
async def submit_test_task():
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        "Origin": "https://www.itdog.cn"
    }

    # 发送 POST 请求
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=form_data, headers=headers) as resp:
            html_content = await resp.text()
            return html_content

# -----------------------------
# 2. 提取 task_id
# -----------------------------
def extract_task_id(html_content):
    # 使用正则表达式提取 task_id
    task_id_match = re.search(r"var task_id='([a-z0-9]+)';", html_content)
    if not task_id_match:
        raise ValueError("未找到 task_id")
    return task_id_match.group(1)

# -----------------------------
# 3. 建立 WebSocket 连接并接收测试结果
# -----------------------------
async def ws_test(task_id):
    wss_url = 'wss://www.itdog.cn/websockets'

    # 建立 WebSocket 连接
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(wss_url) as ws:
            # 发送订阅消息
            subscribe_msg = json.dumps({
                "task_id": task_id
            })
            await ws.send_str(subscribe_msg)

            print("等待测试结果...")
            # 监听 WebSocket 消息
            async for message in ws:
                data = json.loads(message.data)
                if data.get("type") == "success":
                    # 输出节点测试结果
                    print(f"Node: {data['name']}, IP: {data['ip']}, HTTP: {data['http_code']}, Time: {data['all_time']}s")
                elif data.get("type") == "finished":
                    print("测试完成！")
                    break

# -----------------------------
# 4. 运行异步任务
# -----------------------------
async def main():
    html_content = await submit_test_task()  # 提交任务并获取 HTML 内容
    task_id = extract_task_id(html_content)  # 提取 task_id
    print(f"任务 ID: {task_id}")
    await ws_test(task_id)  # 使用 task_id 进行 WebSocket 测试

# 启动事件循环
asyncio.run(main())
