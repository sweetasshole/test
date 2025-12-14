import aiohttp
import asyncio
import re
from aiohttp_socks import ChainProxyConnector  # 使用 ChainProxyConnector

URL = "https://raw.githubusercontent.com/sweetasshole/test/refs/heads/main/sub/CNnodes/rawnodes.txt"
TIMEOUT = 8
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

    if protocol not in ("http", "https", "socks4", "socks5"):
        return None

    if not re.match(r"\d+\.\d+\.\d+\.\d+", ip):
        return None

    if not port.isdigit():
        return None

    return protocol, ip, int(port)

# 创建 aiohttp 连接器
def create_connector(protocol, ip, port):
    if protocol == "http" or protocol == "https":
        return aiohttp.TCPConnector()
    elif protocol == "socks4" or protocol == "socks5":
        return ChainProxyConnector.from_url(f"socks5://{ip}:{port}" if protocol == "socks5" else f"socks4://{ip}:{port}")
    return None

# 验证代理是否可用
async def check_proxy(semaphore, session, protocol, ip, port):
    async with semaphore:  # 在信号量范围内运行
        connector = create_connector(protocol, ip, port)
        if not connector:
            return None

        try:
            async with session.get(TEST_URL, connector=connector, timeout=TIMEOUT) as r:
                if r.status == 200:
                    return f"{protocol}://{ip}:{port}"
        except Exception:
            pass
        return None

# 主函数
async def main():
    # 获取代理列表
    proxy_list = await fetch_proxy_list()
    lines = proxy_list.splitlines()

    proxies = []
    for line in lines:
        result = parse_proxy(line)
        if result:
            proxies.append(result)

    print(f"共解析到 {len(proxies)} 个代理，开始验证...\n")

    alive = []

    # 创建信号量，限制最多 10 个并发
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # 使用 aiohttp 客户端会话进行请求
    async with aiohttp.ClientSession() as session:
        tasks = [check_proxy(semaphore, session, p[0], p[1], p[2]) for p in proxies]
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
