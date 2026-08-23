import psutil, os, glob, time

def execute(params=None):
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    dbs = glob.glob(r'D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\*.db')
    return {
        'status': 'SUCCESS',
        'cpu_usage': f'{cpu}%',
        'ram_usage': f'{ram}%',
        'active_dbs': [os.path.basename(db) for db in dbs],
        'timestamp': time.time(),
        'message': f'Diagnostica sistema: CPU {cpu}%, RAM {ram}%, {len(dbs)} Database integri.'
    }
