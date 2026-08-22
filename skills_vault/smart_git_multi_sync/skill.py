import os, subprocess, time, shutil, glob

PROJECT_ROOT = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio"
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "cerebro-jarvis-dashboard")
BACKUP_VAULT = os.path.join(DASHBOARD_DIR, "backups")
os.makedirs(BACKUP_VAULT, exist_ok=True)

def execute(params=None):
    params = params or {}
    mode = params.get("mode", "sync_all")
    results = []
    
    # 1. Auto-Backup SQLite databases
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    db_files = glob.glob(os.path.join(DASHBOARD_DIR, "*.db"))
    for db in db_files:
        dest = os.path.join(BACKUP_VAULT, f"{os.path.basename(db)}.{timestamp}.bak")
        try:
            shutil.copy(db, dest)
            results.append(f"DB Backup: {os.path.basename(db)} -> OK")
        except Exception as e:
            results.append(f"DB Backup Error {os.path.basename(db)}: {str(e)}")
            
    # 2. Check & Sync Git repos
    subfolders = [os.path.join(PROJECT_ROOT, d) for d in os.listdir(PROJECT_ROOT) if os.path.isdir(os.path.join(PROJECT_ROOT, d))]
    for folder in subfolders:
        git_dir = os.path.join(folder, ".git")
        folder_name = os.path.basename(folder)
        
        # If not a git repo and requested, we can initialize it
        if not os.path.exists(git_dir):
            if folder_name in ["cerebro-jarvis-dashboard", "traslochiwork", "siti-web"]:
                try:
                    subprocess.run(["git", "init"], cwd=folder, capture_output=True, timeout=5)
                    subprocess.run(["git", "add", "."], cwd=folder, capture_output=True, timeout=10)
                    subprocess.run(["git", "commit", "-m", f"Auto-Sync initial backup: {timestamp}"], cwd=folder, capture_output=True, timeout=10)
                    results.append(f"Repo [{folder_name}]: Git Initialized & Committed OK")
                except Exception as e:
                    results.append(f"Repo [{folder_name}] Init Error: {str(e)}")
            continue
            
        try:
            status = subprocess.run(["git", "status", "-s"], cwd=folder, capture_output=True, text=True, timeout=5)
            if status.stdout.strip():
                subprocess.run(["git", "add", "."], cwd=folder, capture_output=True, timeout=10)
                msg = f"Auto-Sync Ecosistema JARVIS: {timestamp}"
                commit = subprocess.run(["git", "commit", "-m", msg], cwd=folder, capture_output=True, text=True, timeout=10)
                results.append(f"Repo [{folder_name}]: Modifiche sincronizzate & committate OK ({commit.returncode})")
            else:
                results.append(f"Repo [{folder_name}]: Pulito / Nessuna modifica pendente")
        except Exception as e:
            results.append(f"Repo [{folder_name}] Sync Error: {str(e)}")
            
    return {
        "status": "SUCCESS",
        "timestamp": timestamp,
        "summary": results,
        "message": f"Sincronizzazione multi-repo e backup completati ({len(results)} operazioni eseguite)."
    }

if __name__ == "__main__":
    import json
    print(json.dumps(execute(), indent=2))
