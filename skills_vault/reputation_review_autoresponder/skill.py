def handle_review(name='Cliente', stars=5, text='Ottimo servizio'):
    stars = int(stars)
    if stars >= 4:
        reply = f'Grazie di cuore {name} per la recensione a 5 stelle! Il team di Pietro Traslochi resta sempre a tua disposizione.'
        sent = 'MOLTO_POSITIVO'
    else:
        reply = f'Gentile {name}, ci dispiace per il problema. Contatta direttamente Badr per risolverlo subito.'
        sent = 'CRITICO'
    return {'status': 'SUCCESS', 'reviewer': name, 'stars': stars, 'sentiment': sent, 'suggested_reply': reply}

def execute(params=None):
    params = params or {}
    return handle_review(params.get('name', 'Mario'), params.get('stars', 5), params.get('text', ''))

if __name__ == '__main__':
    print(execute())
