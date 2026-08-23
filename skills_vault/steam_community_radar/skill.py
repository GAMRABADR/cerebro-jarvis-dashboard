import requests, time

def execute(params=None):
    params = params or {}
    target_game = params.get("game", "dayz").lower()
    
    # Steam AppIDs: DayZ = 221100, Rust = 252490, SCUM = 513710, EBGS = 2886940
    app_map = {
        "dayz": ("221100", "DayZ"),
        "rust": ("252490", "Rust"),
        "scum": ("513710", "SCUM"),
        "ebgs": ("2886940", "EBGS Survival MMO")
    }
    
    app_id, game_name = app_map.get(target_game, ("221100", "DayZ"))
    
    try:
        url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={app_id}&count=3&maxlength=300&format=json"
        res = requests.get(url, timeout=6).json()
        news_items = res.get("appnews", {}).get("newsitems", [])
        
        extracted = []
        for n in news_items:
            extracted.append({
                "title": n.get("title"),
                "url": n.get("url"),
                "date": time.strftime("%d/%m/%Y", time.localtime(n.get("date", time.time()))),
                "snippet": n.get("contents", "")[:180] + "..."
            })
            
        return {
            "status": "SUCCESS",
            "game": game_name,
            "appid": app_id,
            "recent_news_count": len(extracted),
            "news": extracted,
            "message": f"Estratte {len(extracted)} ultime patch notes per {game_name}."
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Errore recupero news Steam: {str(e)}"}

if __name__ == "__main__":
    print(execute({"game": "dayz"}))
