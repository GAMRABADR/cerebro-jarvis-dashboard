def execute(params):
    topic = params.get("topic", "General Patch")
    return {
        "status": "SUCCESS",
        "app_id": "2886940",
        "engine": "Unreal Engine 5.8",
        "message": "Operazione Steamworks completata con successo per: " + str(topic)
    }
