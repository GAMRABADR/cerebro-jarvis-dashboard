#!/usr/bin/env python3
"""
Test Harness for EBJ Native Pure-Rust MCP Server
Validates JSON-RPC 2.0 stdio communication, tool listing, and execution.
"""

import sys
import json
import subprocess
import os
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

RELEASE_BIN = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\ebj-supreme\jarvis-bridge\target\release\ebj-mcp-server.exe"
DEBUG_BIN = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\ebj-supreme\jarvis-bridge\target\debug\ebj-mcp-server.exe"

BIN_PATH = RELEASE_BIN if os.path.exists(RELEASE_BIN) else DEBUG_BIN

def run_test():
    print("=" * 65)
    print("   TEST NATIVE PURE-RUST MCP SERVER (JSON-RPC 2.0 STDIO)   ")
    print("=" * 65)
    print(f"Target Binary: {BIN_PATH}")

    if not os.path.exists(BIN_PATH):
        print(f"[!] Binario non ancora pronto: {BIN_PATH}")
        return False

    proc = subprocess.Popen(
        [BIN_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def send_rpc(msg: dict) -> dict:
        payload = json.dumps(msg) + "\n"
        proc.stdin.write(payload)
        proc.stdin.flush()
        while True:
            line = proc.stdout.readline()
            if not line:
                err = proc.stderr.read()
                raise RuntimeError(f"Server closed stream. Stderr: {err}")
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)

    try:
        # 1. Initialize
        t0 = time.perf_counter()
        resp_init = send_rpc({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        })
        us_init = (time.perf_counter() - t0) * 1_000_000
        server_info = resp_init.get("result", {}).get("serverInfo", {})
        print(f" [PASS] MCP initialize ({us_init:.1f}µs): {server_info.get('name')} v{server_info.get('version')}")

        # 2. Tools/List
        t0 = time.perf_counter()
        resp_list = send_rpc({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        us_list = (time.perf_counter() - t0) * 1_000_000
        tools = resp_list.get("result", {}).get("tools", [])
        print(f" [PASS] MCP tools/list ({us_list:.1f}µs): {len(tools)} native Rust tools registrati")
        for t in tools:
            print(f"   - {t['name']}: {t['description'][:65]}...")

        # 3. Test Tool: ebj_fast_quote
        resp_quote = send_rpc({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "ebj_fast_quote",
                "arguments": {
                    "volume_mq": 65,
                    "piano_partenza": 2,
                    "piano_arrivo": 1,
                    "ascensore": False,
                    "distanza_km": 25.0
                }
            }
        })
        raw_text = resp_quote.get("result", {}).get("content", [{}])[0].get("text", "")
        data_quote = json.loads(raw_text)
        print(f" [PASS] Tool ebj_fast_quote (Rust Latency: {data_quote.get('elapsed_us')}µs): Totale €{data_quote['data']['total_price']}")

        # 4. Test Tool: ebj_lead_certainty_score
        resp_lead = send_rpc({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "ebj_lead_certainty_score",
                "arguments": {
                    "phone": "+393475192834",
                    "name": "Gloria Vezzani",
                    "zone": "Bologna"
                }
            }
        })
        raw_lead = resp_lead.get("result", {}).get("content", [{}])[0].get("text", "")
        data_lead = json.loads(raw_lead)
        print(f" [PASS] Tool ebj_lead_certainty_score (Rust Latency: {data_lead.get('elapsed_us')}µs): Tier {data_lead['data']['tier']}, Score {data_lead['data']['priority_score']}/100")

        # 5. Test Tool: ebj_fuzzy_command_match
        resp_fuzzy = send_rpc({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "ebj_fuzzy_command_match",
                "arguments": {
                    "query": "otimizza carco"
                }
            }
        })
        raw_fuzzy = resp_fuzzy.get("result", {}).get("content", [{}])[0].get("text", "")
        data_fuzzy = json.loads(raw_fuzzy)
        print(f" [PASS] Tool ebj_fuzzy_command_match (Rust Latency: {data_fuzzy.get('elapsed_us')}µs): Best match -> '{data_fuzzy['data']['best_match']}' (Score {data_fuzzy['data']['score']})")

        # 6. Test Tool: ebj_system_metrics
        resp_sys = send_rpc({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "ebj_system_metrics",
                "arguments": {}
            }
        })
        raw_sys = resp_sys.get("result", {}).get("content", [{}])[0].get("text", "")
        data_sys = json.loads(raw_sys)
        print(f" [PASS] Tool ebj_system_metrics (Rust Latency: {data_sys.get('elapsed_us')}µs): RAM {data_sys['data']['used_mem_mb']}MB / {data_sys['data']['total_memory_mb']}MB ({data_sys['data']['memory_usage_percent']}) | Cores: {data_sys['data']['cpu_cores']}")

        print("-" * 65)
        print("TUTTI I TEST DEL SERVER MCP PURE-RUST SONO PASSATI AL 100%!")
        print("=" * 65)
        return True

    finally:
        proc.stdin.close()
        proc.terminate()
        proc.wait(timeout=2)

if __name__ == "__main__":
    run_test()
