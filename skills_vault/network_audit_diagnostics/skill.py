"""
Network Audit & Diagnostic Sentinel (Kali Sandbox On-Demand)
Esegue controlli di rete, verifica di porte e diagnostica DNS
avviando e fermando on-demand il container isolato Kali Linux su VPS Oracle.
"""
import subprocess
import json
import time
import re

SSH_KEY = r"C:\Users\Admin\Downloads\ssh-key-2026-08-18.key"
VPS_HOST = "ubuntu@92.4.233.42"

def sanitize_target(target):
    """Sanitizza host o IP per prevenire injection."""
    cleaned = re.sub(r'[^a-zA-Z0-9.-]', '', str(target).strip())
    return cleaned if cleaned else "127.0.0.1"

def run_kali_diagnostic(target="127.0.0.1", scan_type="PORT_AUDIT", ports="22,80,443,5678,8088,9000"):
    """
    Avvia il container, esegue il check diagnostico e spegne immediatamente il container.
    """
    clean_target = sanitize_target(target)
    
    if scan_type == "PORT_AUDIT":
        cmd_inside = f"nmap -sT -T4 -p {ports} {clean_target} -oN /tmp/scan.txt && cat /tmp/scan.txt"
    elif scan_type == "DNS_DIAG":
        cmd_inside = f"dig +short {clean_target} && nslookup {clean_target}"
    elif scan_type == "PING_TRACE":
        cmd_inside = f"ping -c 3 {clean_target} && traceroute -m 8 {clean_target}"
    else:
        cmd_inside = f"nmap -F {clean_target}"

    remote_exec = (
        f"docker start kali-sandbox >/dev/null 2>&1 && "
        f"docker exec kali-sandbox sh -c \"{cmd_inside}\" ; "
        f"docker stop kali-sandbox >/dev/null 2>&1"
    )

    t0 = time.time()
    try:
        res = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-i", SSH_KEY, VPS_HOST, remote_exec],
            capture_output=True, text=True, timeout=45
        )
        latency_ms = round((time.time() - t0) * 1000, 2)
        raw_output = res.stdout if res.stdout else res.stderr
        
        # Simple parser for nmap results
        open_ports = []
        for line in raw_output.splitlines():
            if "/tcp" in line and "open" in line:
                parts = line.split()
                open_ports.append({
                    "port": parts[0],
                    "state": parts[1] if len(parts) > 1 else "open",
                    "service": parts[2] if len(parts) > 2 else "unknown"
                })

        return {
            "status": "SUCCESS" if res.returncode == 0 else "PARTIAL",
            "target": clean_target,
            "scan_type": scan_type,
            "latency_ms": latency_ms,
            "open_ports": open_ports,
            "raw_output": raw_output[:2000]
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "target": clean_target,
            "error": str(e),
            "latency_ms": round((time.time() - t0) * 1000, 2)
        }

if __name__ == "__main__":
    import sys
    tgt = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    st = sys.argv[2] if len(sys.argv) > 2 else "PORT_AUDIT"
    print(json.dumps(run_kali_diagnostic(tgt, st), indent=2))
