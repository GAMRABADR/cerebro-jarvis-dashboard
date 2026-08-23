import os, json, time

MEDIA_OUT_DIR = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\media_out"
os.makedirs(MEDIA_OUT_DIR, exist_ok=True)

def execute(params=None):
    params = params or {}
    video_path = params.get("video_path", "clip_ebgs_sample.mp4")
    title = params.get("title", "EBGS Survival: Devlog #14 - New Physics & Building System")
    description = params.get("description", "Nuovo gameplay e devlog ufficiale Unreal Engine 5.8 per EBGS Survival MMO.")
    privacy = params.get("privacy", "public")
    
    deploy_manifest = {
        "channel_id": "UCLcxINhwr6_SVdor8zCADpg",
        "channel_name": "EBGStudio",
        "title": title,
        "description": description + "\n\nWishlist on Steam: https://store.steampowered.com/app/2886940",
        "tags": ["DayZ", "Rust", "UnrealEngine5", "EBGS", "IndieGame", "Survival"],
        "category_id": 20, # Gaming
        "privacy_status": privacy,
        "timestamp": time.time(),
        "status": "QUEUED_FOR_DISPATCH"
    }
    
    out_file = os.path.join(MEDIA_OUT_DIR, f"yt_deploy_{int(time.time())}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(deploy_manifest, f, indent=2)
        
    return {
        "status": "SUCCESS",
        "channel": "EBGStudio",
        "deploy_file": out_file,
        "title": title,
        "message": f"Pacchetto di pubblicazione per '{title}' generato con successo per il canale EBGStudio."
    }

if __name__ == "__main__":
    print(execute())
