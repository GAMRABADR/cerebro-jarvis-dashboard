import subprocess
import re
import os
import json

def get_wifi_status():
    try:
        p = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5)
        out = p.stdout
        ssid_m = re.search(r'SSID\s*:\s*(.+)', out)
        signal_m = re.search(r'Segnale|Signal\s*:\s*(.+)', out)
        state_m = re.search(r'Stato|State\s*:\s*(.+)', out)
        
        ssid = ssid_m.group(1).strip() if ssid_m else "Disconnesso"
        signal = signal_m.group(1).strip() if signal_m else "N/A"
        state = state_m.group(1).strip() if state_m else "Sconosciuto"

        # Scan available networks
        p_scan = subprocess.run(["netsh", "wlan", "show", "networks"], capture_output=True, text=True, timeout=5)
        networks = re.findall(r'SSID\s+\d+\s+:\s+(.+)', p_scan.stdout)

        return {
            "status": "SUCCESS",
            "connected_ssid": ssid,
            "signal_strength": signal,
            "connection_state": state,
            "available_networks": [n.strip() for n in networks[:8]]
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Errore Wi-Fi: {str(e)}"}

def get_bluetooth_devices():
    try:
        ps_cmd = "Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName, Status, Present | ConvertTo-Json"
        p = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=6)
        if p.stdout:
            data = json.loads(p.stdout)
            if isinstance(data, dict): data = [data]
            devices = []
            for d in data:
                name = d.get("FriendlyName", "")
                if name and not any(k in name.lower() for k in ["enumerator", "enumeratore", "protocol", "generic", "generico"]):
                    devices.append({
                        "name": name,
                        "status": d.get("Status", "OK"),
                        "connected": d.get("Present", True)
                    })
            return {
                "status": "SUCCESS",
                "total_bluetooth_devices": len(devices),
                "devices": devices[:10]
            }
    except Exception as e:
        return {"status": "ERROR", "message": f"Errore Bluetooth: {str(e)}"}
    return {"status": "SUCCESS", "devices": []}

def execute(params=None):
    params = params or {}
    mode = params.get("mode", "all")
    
    res = {}
    if mode in ["all", "wifi"]:
        res["wifi"] = get_wifi_status()
    if mode in ["all", "bluetooth", "bt"]:
        res["bluetooth"] = get_bluetooth_devices()
        
    return {
        "status": "SUCCESS",
        "controller": "FastMCP Bluetooth & Wi-Fi Gateway",
        "result": res
    }

if __name__ == "__main__":
    import json
    print(json.dumps(execute(), indent=2))
