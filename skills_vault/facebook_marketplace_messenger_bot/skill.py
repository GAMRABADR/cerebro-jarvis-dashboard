def handle_fb_message(sender='Utente FB', msg='E ancora disponibile?'):
    reply = f'Ciao {sender}! Si, il servizio sgomberi e traslochi e attivo. Da quale comune a quale comune ti serve il trasporto?'
    return {'status': 'SUCCESS', 'sender': sender, 'lead_type': 'HOT_LEAD', 'reply': reply}

def execute(params=None):
    params = params or {}
    return handle_fb_message(params.get('sender', 'Marco'), params.get('msg', 'disponibile'))

if __name__ == '__main__':
    print(execute())
