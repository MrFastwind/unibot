import json
from os import environ, path

sent = []
sent_file = path.join(path.dirname(environ['DB_PATH']), 'sent_announcements.json')
if path.isfile(sent_file):
    with open(sent_file, 'r') as f:
        sent = json.load(f)

announcements = []

announcements.append({
    'seq': 0,
    'msg': ("UniBot è stato aggiornato! 🎉🎉\n"
            "Ora puoi scegliere l'orario di avviso, prova subito con /ricordami")
})

def get_announcements():
    announcements.sort(key=lambda a: a['seq'])
    return [a for a in announcements if a['seq'] not in sent]

def set_sent(msg):
    sent.append(msg['seq'])

def save_sent():
    with open(sent_file, 'w') as f:
        json.dump(sent, f)
