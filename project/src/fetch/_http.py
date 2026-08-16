"""
共享 HTTP 请求辅助函数。

本项目原计划用 Python 标准库 urllib / requests 发请求，但在执行环境的出站代理下
实测两者都会间歇性挂起或报 HTTP/2 流错误(curl error 92: "HTTP/2 stream ... was
not closed cleanly")。根本原因：该会话的出站代理重新终结TLS后，对下游的HTTP/2
ALPN协商不稳定。强制用 HTTP/1.1 (--http1.1) 后 curl 100%稳定(亚秒级返回)，
Python urllib/requests 默认走的协商路径命中同一个bug所以同样会挂。
统一改为通过 subprocess 调用 curl --http1.1 发请求。在没有这层代理的普通环境中，
这个实现同样可以正常工作(--http1.1只是放弃HTTP/2升级，不影响功能)。
"""

import json
import subprocess
import time
from urllib.parse import urlencode


def curl_get(url: str, params: dict | None = None, headers: dict | None = None,
             timeout: int = 15, retries: int = 6) -> bytes:
    """GET 请求，返回响应体 bytes。非2xx抛 RuntimeError。"""
    full_url = url
    if params:
        full_url = f"{url}?{urlencode(params, doseq=True)}"

    cmd = ["curl", "--http1.1", "-sS", "-m", str(timeout), "-w", "\n__HTTP_STATUS__:%{http_code}"]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    cmd.append(full_url)

    last_err = None
    for attempt in range(retries):
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
            out = result.stdout
            marker = b"\n__HTTP_STATUS__:"
            idx = out.rfind(marker)
            if idx == -1:
                last_err = RuntimeError(f"curl 输出格式异常: {result.stderr[:300]!r}")
                time.sleep(2 ** attempt)
                continue
            body = out[:idx]
            status = int(out[idx + len(marker):].decode().strip())
            if 200 <= status < 300:
                return body
            last_err = RuntimeError(f"HTTP {status} for {full_url}: {body[:300]!r}")
            if 400 <= status < 500:
                # 4xx是明确的客户端错误(如404资源不存在)，重试不会改变结果，直接放弃
                raise last_err
        except subprocess.TimeoutExpired as e:
            last_err = e
        time.sleep(min(2 ** attempt, 8))
    raise last_err


def curl_get_json(url: str, params: dict | None = None, headers: dict | None = None,
                   timeout: int = 20, retries: int = 6):
    body = curl_get(url, params=params, headers=headers, timeout=timeout, retries=retries)
    return json.loads(body.decode())


def curl_post_json(url: str, payload: dict, headers: dict | None = None,
                    timeout: int = 20, retries: int = 6):
    cmd = ["curl", "--http1.1", "-sS", "-m", str(timeout), "-w", "\n__HTTP_STATUS__:%{http_code}",
           "-X", "POST", "-H", "Content-Type: application/json"]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    cmd += ["-d", json.dumps(payload), url]

    last_err = None
    for attempt in range(retries):
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
            out = result.stdout
            marker = b"\n__HTTP_STATUS__:"
            idx = out.rfind(marker)
            if idx == -1:
                last_err = RuntimeError(f"curl 输出格式异常: {result.stderr[:300]!r}")
                time.sleep(2 ** attempt)
                continue
            body = out[:idx]
            status = int(out[idx + len(marker):].decode().strip())
            if 200 <= status < 300:
                return json.loads(body.decode())
            last_err = RuntimeError(f"HTTP {status} for {url}: {body[:300]!r}")
            if 400 <= status < 500:
                raise last_err
        except subprocess.TimeoutExpired as e:
            last_err = e
        time.sleep(min(2 ** attempt, 8))
    raise last_err
