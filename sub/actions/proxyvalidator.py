import aiohttp
import asyncio
import re

URL = "https://raw.githubusercontent.com/sweetasshole/test/refs/heads/main/sub/CNnodes/rawnodes.txt"
TIMEOUT = 8
THREADS = 20
MAX_CONCURRENT = 10  # 最大并发数，限制同时验证的代理数量

TEST_URL = "https://gstatic.com/generate_204"

# 获取代理列表
async def fetch_proxy_list():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.text()

# 解析代理信息
def parse_proxy(line):
    """
    解析格式：
    http 39.102.209.121 8081 高匿 北京市 阿里云 ...
    """
    parts = re.split(r"\s+", line.strip())
    if len(parts) < 3:
        return None

    protocol, ip, port = parts[0], parts[1], parts[2]

    if protocol not in ("http", "https"):
        return None

    if not re.match(r"\d+\.\d+\.\d+\.\d+", ip):
        return None

    if not port.isdigit():
        return None

    return f"{protocol}://{ip}:{port}"

# 验证代理是否可用
async def check_proxy(semaphore, session, proxy):
    async with semaphore:  # 在信号量范围内运行
        proxies = {
            "http": proxy,
            "https": proxy
        }
        try:
            async with session.get(TEST_URL, proxies=proxies, timeout=TIMEOUT) as r:
                if r.status == 200:
                    return proxy
        except Exception:
            pass
        return None

# 主函数
async def main():
    # 获取代理列表
    proxy_list = await fetch_proxy_list()
    lines = proxy_list.splitlines()

    proxies = [parse_proxy(line) for line in lines if parse_proxy(line)]

    print(f"共解析到 {len(proxies)} 个代理，开始验证...\n")

    alive = []

    # 创建信号量，限制最多 10 个并发
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # 使用 aiohttp 客户端会话进行请求
    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(semaphore, session, p) for p in proxies]
        for result in await asyncio.gather(*tasks):
            if result:
                alive.append(result)
                print("[OK]", result)

    print("\n可用代理列表：")
    for p in alive:
        print(p)

    print(f"\n存活数量：{len(alive)}")

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())
