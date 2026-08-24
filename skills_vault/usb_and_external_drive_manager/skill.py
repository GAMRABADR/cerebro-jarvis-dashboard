import os
import shutil
import ctypes
import string
import datetime
import json
import psutil

def scan_all_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drive_path = f"{letter}:\\"
            drive_type_code = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
            type_name = {
                2: "REMOVABLE_USB_OR_SD",
                3: "FIXED_DRIVE_INTERNAL_SSD_HDD",
                4: "NETWORK_SHARED_DRIVE",
                5: "CDROM_OPTICAL"
            }.get(drive_type_code, "UNKNOWN")
            
            usage_dict = {}
            try:
                u = psutil.disk_usage(drive_path)
                usage_dict = {
                    "total_gb": round(u.total / (1024**3), 1),
                    "used_gb": round(u.used / (1024**3), 1),
                    "free_gb": round(u.free / (1024**3), 1),
                    "used_percent": f"{u.percent}%"
                }
            except Exception:
                pass
                
            drives.append({
                "drive_letter": f"{letter}:",
                "path": drive_path,
                "type": type_name,
                "is_removable_usb": drive_type_code == 2,
                "storage": usage_dict
            })
        bitmask >>= 1
    return drives

def read_usb_contents(drive_letter=None, max_files=40):
    all_drives = scan_all_drives()
    
    # Auto-select removable USB if not specified, otherwise default to E: or first secondary drive
    target_drive = None
    if drive_letter:
        target_drive = f"{drive_letter.rstrip(':').upper()}:\\"
    else:
        usb_drives = [d for d in all_drives if d["is_removable_usb"]]
        if usb_drives:
            target_drive = usb_drives[0]["path"]
        elif len(all_drives) > 2:
            target_drive = all_drives[-1]["path"] # e.g. E:\
        else:
            target_drive = all_drives[0]["path"]
            
    if not os.path.exists(target_drive):
        return {"status": "ERROR", "message": f"Unità '{target_drive}' non accessibile o disconnessa."}
        
    items = []
    try:
        with os.scandir(target_drive) as it:
            for entry in it:
                try:
                    is_d = entry.is_dir()
                    sz = 0 if is_d else entry.stat().st_size
                    sz_str = "<DIR>" if is_d else f"{sz/(1024*1024):.2f} MB" if sz > 1024*1024 else f"{sz/1024:.1f} KB"
                    mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
                    items.append({
                        "name": entry.name,
                        "is_dir": is_d,
                        "size": sz_str,
                        "modified": mtime,
                        "path": entry.path
                    })
                except Exception:
                    pass
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return {
            "status": "SUCCESS",
            "drive": target_drive,
            "total_items": len(items),
            "items": items[:max_files],
            "message": f"Esplorazione unità {target_drive} completata: {len(items)} elementi trovati."
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def backup_vault_to_usb(drive_letter=None):
    all_drives = scan_all_drives()
    target_drive = f"{drive_letter.rstrip(':').upper()}:\\" if drive_letter else ("E:\\" if os.path.exists("E:\\") else "D:\\")
    
    backup_dir = os.path.join(target_drive, "JARVIS_USB_BACKUPS", datetime.datetime.now().strftime("%Y%m%d_%H%M"))
    os.makedirs(backup_dir, exist_ok=True)
    
    db_sources = [
        r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\mail_vault.db",
        r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\hermes_ltm_memory.db",
        r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\hermes_kanban.db",
        r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\HOLOGRAPHIC_MEMORY_VAULT.md"
    ]
    
    copied = []
    for db in db_sources:
        if os.path.exists(db):
            dst = os.path.join(backup_dir, os.path.basename(db))
            shutil.copy2(db, dst)
            copied.append(os.path.basename(db))
            
    return {
        "status": "SUCCESS",
        "backup_destination": backup_dir,
        "files_backed_up": copied,
        "message": f"Snapshot dei database e memoria LTM salvato con successo su USB in: '{backup_dir}'"
    }

def execute(params=None):
    params = params or {}
    action = params.get("action", "scan").lower()
    
    if action in ["scan", "list_drives", "drives", "unita"]:
        return {"status": "SUCCESS", "drives": scan_all_drives()}
    elif action in ["read", "read_usb", "explore_usb", "leggi_usb", "apri_usb"]:
        return read_usb_contents(params.get("drive"))
    elif action in ["backup", "backup_usb", "salva_su_usb"]:
        return backup_vault_to_usb(params.get("drive"))
    else:
        return {"status": "SUCCESS", "drives": scan_all_drives()}

if __name__ == "__main__":
    print(execute({"action": "scan"}))
    print(execute({"action": "read"}))
