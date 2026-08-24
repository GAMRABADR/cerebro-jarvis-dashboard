import urllib.parse

def calculate_route(dep='Imola', dest='Bologna', mq=50, piano_p=2, piano_a=1, asc=True):
    distances = {
        ('Imola', 'Bologna'): (38.5, 35, 2.80),
        ('Imola', 'Faenza'): (17.2, 20, 1.40),
        ('Imola', 'Forli'): (31.0, 30, 2.20),
        ('Imola', 'Castel San Pietro'): (12.5, 15, 0.0),
        ('Imola', 'Ravenna'): (44.0, 42, 3.10),
        ('Bologna', 'Milano'): (215.0, 140, 16.50),
        ('Imola', 'Milano'): (250.0, 165, 19.30)
    }
    k = (dep.strip().title(), dest.strip().title())
    rk = (dest.strip().title(), dep.strip().title())
    km, mins, toll = distances.get(k, distances.get(rk, (45.0, 40, 3.50)))
    
    base = mq * 8.0
    scale = 0.0 if asc else (piano_p + piano_a) * mq * 0.5
    trasf = round(km * 1.20, 2)
    tot = round(base + scale + trasf + toll + 60.0, 2)
    
    return {
        'status': 'SUCCESS',
        'partenza': dep, 'arrivo': dest, 'distanza_km': km, 'minuti': mins,
        'pedaggio_euro': toll, 'preventivo_totale': tot,
        'maps_url': f'https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(dep)}&destination={urllib.parse.quote(dest)}'
    }

def execute(params=None):
    params = params or {}
    return calculate_route(params.get('partenza', 'Imola'), params.get('arrivo', 'Bologna'), params.get('mq', 50))

if __name__ == '__main__':
    print(execute())
