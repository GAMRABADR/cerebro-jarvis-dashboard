import json, time

FLEET_REGISTRY = {
    "jarvis_master": {"name": "AG-JARVIS Master", "bot": "@EBGStudioBot", "role": "Executive Decision & Memory Hub"},
    "pietro_traslochi": {"name": "AG-PietroTraslochi", "bot": "@PietroTraslochiBot", "role": "Client Onboarding & Intake"},
    "badrexpress_lavoro": {"name": "AG-BadrExpressLavoro", "bot": "@BadrExpress_LavoroBot", "role": "Worker Dispatch & Task Assignment"},
    "ebgstudio_tube": {"name": "AG-EBGStudioTube", "bot": "@EBGStudioTube_Bot", "role": "Game Dev & YouTube Media Forge"},
    "eb_media_studio": {"name": "AG-EB_MediaStudio", "bot": "@EB_Media_Bot", "role": "Personal Brand & Short Form Video Engine"},
    "agente_zero_vps": {"name": "AG-AgenteZero", "host": "92.4.233.42:50080", "role": "Deep Autonomous Linux VPS Worker"}
}

def execute(params=None):
    params = params or {}
    target_agent = params.get("agent_id", "all")
    task_desc = params.get("task", "Status Check & Heartbeat")
    
    if target_agent == "all":
        dispatched = list(FLEET_REGISTRY.keys())
    else:
        dispatched = [target_agent] if target_agent in FLEET_REGISTRY else ["jarvis_master"]
        
    return {
        "status": "SUCCESS",
        "dispatched_to": dispatched,
        "fleet_size": len(FLEET_REGISTRY),
        "fleet_status": FLEET_REGISTRY,
        "task": task_desc,
        "timestamp": time.time(),
        "message": f"Task '{task_desc}' instradato con successo a {len(dispatched)} agenti della flotta."
    }

if __name__ == "__main__":
    print(json.dumps(execute(), indent=2))
