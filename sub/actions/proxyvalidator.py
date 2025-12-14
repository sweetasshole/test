import asyncio
import aiohttp
import re
from aiohttp_socks import ProxyConnector

URL = "https://raw.githubusercontent.com/sweetasshole/test/refs/heads/main/sub/CNnodes/rawnodes.txt"
TEST_URL = "https://gstatic.com/generate_204"
TIMEOUT = 8
MAX_CONCURRENT = 10

# 读取代理列表
async def fetch_proxy_list():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.text()

def parse_proxy(line):
    parts = re.split(r"\s+", line.strip())
    if len(parts) < 3:
        return None

    proto, ip, port = parts[0].lower(), parts[1], parts[2]

    if proto not in ("http", "https", "socks4", "socks5"):
        return None
    if not re.match(r"\d+\.\d+\.\d+\.\d+", ip):
        return None
    if not port.isdigit():
        return None

    return f"{proto}://{ip}:{port}"

async def check_proxy(semaphore, proxy_url):
    async with semaphore:
        try:
            connector = ProxyConnector.from_url(proxy_url)
            timeout = aiohttp.ClientTimeout(total=TIMEOUT)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(TEST_URL) as resp:
                    if resp.status == 204 or resp.status == 200:
                        return proxy_url
        except Exception:
            pass
        return None

async def main():
    text = await fetch_proxy_list()
    proxies = [p for p in (parse_proxy(l) for l in text.splitlines()) if p]

    print(f"共解析到 {len(proxies)} 个代理，开始验证...\n")

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [check_proxy(sem, p) for p in proxies]

    alive = []
    for r in await asyncio.gather(*tasks):
        if r:
            alive.append(r)
            print("[OK]", r)

    print("\n存活代理：")
    for p in alive:
        print(p)

    print(f"\n存活数量：{len(alive)}")

if __name__ == "__main__":
    asyncio.run(main())
