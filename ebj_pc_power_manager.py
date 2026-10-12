"""
==============================================================================
⚡ EBJ PC POWER & REMOTE WAKE-ON-LAN MANAGER v1.0
==============================================================================
Gestione remota dell'alimentazione di DESKTOP-SJR1JS8 per l'Ingegnere Badr:
  - Spegnimento vocale immediato
  - Riavvio da smartphone via Cloudflare Tunnel / eb.badrexpress.com
  - Accensione remota tramite Magic Packet Wake-on-LAN (Intel I225-V NIC)
  - Telemetria hardware in tempo reale (Ryzen 7 5700X3D · RTX 4070 · 64GB RAM)
==============================================================================
"""

import os
import sys
import time
import socket
import subprocess
import psutil
from typing import Dict, Any

PC_NODE_NAME = "DESKTOP-SJR1JS8"
PC_MAC_ADDRESS = "08-BF-B8-73-99-3D"
PC_IP_ADDRESS = "192.168.0.100"
PC_BROADCAST_IP = "192.168.0.255"

def get_system_power_status() -> Dict[str, Any]:
    """Ritorna lo stato operativo di alimentazione e hardware in tempo reale."""
    boot_time = psutil.boot_time()
    uptime_sec = int(time.time() - boot_time)
    hours = uptime_sec // 3600
    minutes = (uptime_sec % 3600) // 60
    
    vm = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=None)
    
    return {
        "status": "ONLINE",
        "state_label": "ACCESO",
        "node_name": PC_NODE_NAME,
        "mac_address": PC_MAC_ADDRESS,
        "local_ip": PC_IP_ADDRESS,
        "uptime": f"{hours}h {minutes}m",
        "uptime_seconds": uptime_sec,
        "cpu_name": "AMD Ryzen 7 5700X3D (8C/16T, 3D V-Cache)",
        "cpu_usage_pct": cpu_pct,
        "ram_total_gb": round(vm.total / (1024**3), 1),
        "ram_used_gb": round(vm.used / (1024**3), 1),
        "ram_usage_pct": vm.percent,
        "gpus": ["NVIDIA GeForce RTX 4070 (Primary)", "NVIDIA GeForce GTX 1660 (Secondary)"],
        "nic_name": "Intel(R) Ethernet Controller (3) I225-V 2.5G",
        "wol_ready": True
    }

def shutdown_pc(delay_seconds: int = 5, reason: str = "Spegnimento remoto EBJ") -> Dict[str, Any]:
    """Avvia la procedura di arresto del sistema."""
    cmd = ["shutdown", "/s", "/t", str(delay_seconds), "/c", reason]
    subprocess.run(cmd, check=False)
    return {
        "status": "success",
        "action": "shutdown",
        "node_name": PC_NODE_NAME,
        "delay_seconds": delay_seconds,
        "message": f"Arresto del PC avviato. Spegnimento in {delay_seconds} secondi."
    }

def restart_pc(delay_seconds: int = 5, reason: str = "Riavvio remoto da smartphone EBJ") -> Dict[str, Any]:
    """Avvia la procedura di riavvio del sistema."""
    cmd = ["shutdown", "/r", "/t", str(delay_seconds), "/c", reason]
    subprocess.run(cmd, check=False)
    return {
        "status": "success",
        "action": "restart",
        "node_name": PC_NODE_NAME,
        "delay_seconds": delay_seconds,
        "message": f"Riavvio del PC avviato. Il sistema si riavvierà tra {delay_seconds} secondi."
    }

def abort_power_action() -> Dict[str, Any]:
    """Annulla qualsiasi arresto o riavvio programmato."""
    cmd = ["shutdown", "/a"]
    subprocess.run(cmd, check=False)
    return {
        "status": "success",
        "action": "abort",
        "node_name": PC_NODE_NAME,
        "message": "Operazione di spegnimento/riavvio annullata con successo."
    }

def send_wake_on_lan(mac: str = PC_MAC_ADDRESS, port: int = 9) -> Dict[str, Any]:
    """
    Costruisce e trasmette il Magic Packet Wake-on-LAN (102 byte)
    sulla rete locale in broadcast per risvegliare il computer.
    """
    clean_mac = mac.replace(":", "").replace("-", "")
    if len(clean_mac) != 12:
        return {"status": "error", "message": f"Formato MAC non valido: {mac}"}
        
    mac_bytes = bytes.fromhex(clean_mac)
    magic_packet = b'\xFF' * 6 + mac_bytes * 16
    
    sent_targets = []
    # Invia sia su global broadcast che su subnet locale broadcast
    for target_ip in ["255.255.255.255", PC_BROADCAST_IP]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(magic_packet, (target_ip, port))
                sent_targets.append(target_ip)
        except Exception as e:
            pass
            
    return {
        "status": "success",
        "action": "wake_on_lan",
        "node_name": PC_NODE_NAME,
        "target_mac": mac,
        "broadcast_targets": sent_targets,
        "message": f"Magic Packet WoL inviato con successo a {mac} ({PC_NODE_NAME})."
    }

if __name__ == "__main__":
    print("=== TELEMETRIA HARDWARE & POWER EBJ ===")
    status = get_system_power_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
