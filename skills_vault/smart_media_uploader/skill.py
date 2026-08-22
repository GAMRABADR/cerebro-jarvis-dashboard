import os, json, time, subprocess

MEDIA_OUT_DIR = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\media_out"
os.makedirs(MEDIA_OUT_DIR, exist_ok=True)

def execute(params=None):
    params = params or {}
    title = params.get("title", "EBGS Survival: Hardcore Raid Gameplay")
    description = params.get("description", "Nuovo gameplay e devlog Unreal Engine 5.8 per EBGS Survival MMO.")
    target_platform = params.get("platform", "youtube_shorts")
    tags = params.get("tags", ["DayZ", "Rust", "UnrealEngine5", "EBGS", "Gaming", "Shorts"])
    
    # 1. Structure optimized metadata payload
    payload = {
        "title": title[:100],
        "description": description + "\n\nWishlist on Steam: https://store.steampowered.com/app/2886940\n#shorts #gaming",
        "tags": tags,
        "category_id": "20", # Gaming
        "privacy": "public",
        "formatted_for": target_platform,
        "render_profile": "9:16 Vertical 1080x1920 60FPS H.264",
        "audio_loudness": "-14 LUFS Normalized"
    }
    
    # 2. Save metadata descriptor in media_out
    meta_file = os.path.join(MEDIA_OUT_DIR, f"meta_{int(time.time())}.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    return {
        "status": "SUCCESS",
        "channel_target": "EBGStudio (UCLcxINhwr6_SVdor8zCADpg)",
        "payload": payload,
        "descriptor_path": meta_file,
        "message": f"Pipeline media configurata per '{title}' su {target_platform}."
    }

if __name__ == "__main__":
    print(json.dumps(execute(), indent=2))
