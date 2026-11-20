#!/usr/bin/env python3
"""Record the web-insights MCP tool calls used for the SEO brief example.

Serves the fictional pages in ../input/pages on http://127.0.0.1:3402 and talks
to the web-insights-mcp server over stdio with plain JSON-RPC (no SDK needed).

Usage: WEB_INSIGHTS_CLI=/path/to/web-insights-mcp/dist/cli.js python3 research/collect.py
"""
import json
import os
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGES = HERE.parent / "input" / "pages"
PORT = 3402
BASE = f"http://127.0.0.1:{PORT}"
CLI = os.environ.get("WEB_INSIGHTS_CLI", str(HERE.parents[3] / "web-insights-mcp" / "dist" / "cli.js"))


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if not self.path.endswith((".html", "/")) and "." not in self.path.rsplit("/", 1)[-1]:
            self.path += ".html"
        return super().do_GET()

    def log_message(self, *args):
        pass


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(PAGES)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    env = {"PATH": os.environ.get("PATH", ""), "WEB_INSIGHTS_ALLOW_LOCALHOST": "1"}
    proc = subprocess.Popen(["node", CLI], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
    next_id = 0

    def rpc(method, params=None, notify=False):
        nonlocal next_id
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            next_id += 1
            msg["id"] = next_id
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        if notify:
            return None
        while True:
            reply = json.loads(proc.stdout.readline())
            if reply.get("id") == next_id:
                if "error" in reply:
                    raise RuntimeError(reply["error"])
                return reply["result"]

    rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "seo-brief-example", "version": "1.0"}})
    rpc("notifications/initialized", notify=True)

    ours = f"{BASE}/lumen/cold-brew"
    competitors = {
        "brewlab": f"{BASE}/brewlab/cold-brew-ratio",
        "beanandbarrel": f"{BASE}/beanandbarrel/cold-brew-ratio-test",
        "dailygrind": f"{BASE}/dailygrind/cold-brew-ratio",
    }
    calls = []
    for name, url in {"lumen": ours, **competitors}.items():
        calls.append((f"fetch_page.{name}", "fetch_page", {"url": url, "max_chars": 12000}))
        calls.append((f"extract_structured.{name}", "extract_structured", {"url": url, "include": ["meta", "headings", "json_ld", "tables"]}))
    for name, url in competitors.items():
        calls.append((f"compare_pages.lumen-vs-{name}", "compare_pages", {"url_a": ours, "url_b": url}))
    calls.append(("seo_audit.lumen", "seo_audit", {"url": ours}))

    log = []
    for label, tool, args in calls:
        result = rpc("tools/call", {"name": tool, "arguments": args})
        out = {"tool": tool, "arguments": args, "isError": bool(result.get("isError")), "structuredContent": result.get("structuredContent")}
        (HERE / f"{label}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log.append(f"{label}: {'ERROR' if out['isError'] else 'ok'}")
    proc.stdin.close()
    proc.wait(timeout=10)
    server.shutdown()
    (HERE / "calls.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
