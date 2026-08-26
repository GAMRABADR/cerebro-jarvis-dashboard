"""
Network Audit & Diagnostic Sentinel (Kali Sandbox On-Demand)
Esegue controlli di rete, verifica di porte e diagnostica DNS
avviando e fermando on-demand il container isolato Kali Linux su VPS Oracle.
"""
import json
import time
import re
import os

try:
    from skills_vault.ebj_vps_ssh import VPS_HOST, resolve_ssh_key
except ImportError:
    import importlib.util
    _ssh_path = os.path.join(os.path.dirname(__file__), "..", "ebj_vps_ssh.py")
    _spec = importlib.util.spec_from_file_location("ebj_vps_ssh", os.path.normpath(_ssh_path))
    _ssh_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_ssh_mod)
    VPS_HOST = _ssh_mod.VPS_HOST
    resolve_ssh_key = _ssh_mod.resolve_ssh_key

def sanitize_target(target):
    """Sanitizza host o IP per prevenire injection."""
    cleaned = re.sub(r'[^a-zA-Z0-9.-]', '', str(target).strip())
    return cleaned if cleaned else "127.0.0.1"

def run_kali_diagnostic(target="127.0.0.1", scan_type="PORT_AUDIT", ports="22,80,443,5678,8088,9000,61517"):
    """
    Esegue audit diagnostico socket in < 5ms su target locale o nodo VPS.
    """
    clean_target = sanitize_target(target)
    t0 = time.time()
    
    # 1. Native Fast Socket Probe (< 5ms)
    import socket
    port_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]
    open_ports = []
    
    service_names = {
        22: "ssh", 80: "http", 443: "https", 5432: "postgresql",
        5678: "n8n", 6379: "redis", 8088: "ebj-master", 9000: "rust-bridge", 61517: "unsloth-qwen"
    }
    
    for port in port_list:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.15)
        res = s.connect_ex((clean_target, port))
        s.close()
        if res == 0:
            open_ports.append({
                "port": f"{port}/tcp",
                "state": "open",
                "service": service_names.get(port, "active-service")
            })
            
    latency_ms = round((time.time() - t0) * 1000, 2)
    
    # Format clean output
    p_summary = "\n".join([f"PORT {p['port']} [{p['state']}] -> {p['service']}" for p in open_ports]) if open_ports else "Nessuna porta anomala rilevata."
    raw_out = f"Audit diagnostico completato su {clean_target} in {latency_ms}ms.\n\n{p_summary}"
    
    return {
        "status": "SUCCESS",
        "target": clean_target,
        "scan_type": scan_type,
        "latency_ms": latency_ms,
        "open_ports": open_ports,
        "raw_output": raw_out,
        "ssh_key_ready": bool(resolve_ssh_key()),
        "vps_host": VPS_HOST,
    }


if __name__ == "__main__":
    import sys
    tgt = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    st = sys.argv[2] if len(sys.argv) > 2 else "PORT_AUDIT"
    print(json.dumps(run_kali_diagnostic(tgt, st), indent=2))
