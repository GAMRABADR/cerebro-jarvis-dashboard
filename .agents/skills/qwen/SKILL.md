---
name: qwen
description: Esegue richieste e genera risposte tramite il modello locale Qwen 3.8 27B su Unsloth GPU (porta 61517).
---

# Qwen 3.8 Local AI Skill

Quando l'utente invoca /qwen o chiede di usare il modello locale:
1. Inoltra il prompt al server locale Unsloth su porta 61517 con script qwen.py.
2. Restituisci la risposta generata dalla GPU locale dell'Ingegner Badr.
