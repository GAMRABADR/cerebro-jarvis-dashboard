import sqlite3

conn = sqlite3.connect('mail_vault.db')
c = conn.cursor()

# Normalizziamo le citta esistenti di Bologna
c.execute("UPDATE b2b_car_washes SET city = 'Bologna' WHERE city = 'Bologna/Romagna' OR city IS NULL")

milano_leads = [
    ('Milano', 'Wash Out Milano Hub', '02 82956740', 'Via Tertulliano 70, Milano Centro', 'DETAILING/B2B', 'Milano Centro & Sud', '~3 km dal centro', '390282956740', 'Lavaggio a secco e flotta mobile, alto potenziale detergenti ecologici'),
    ('Milano', 'Autolavaggio Darsena Express', '02 8323671', 'Viale Gorizia 14, Milano Navigli', 'MANO/SANIFICAZIONE', 'Milano Navigli & Porta Genova', '~2 km dal centro', '39028323671', 'Lavaggio a mano continuativo, consumo costante di shampoo neutro e nero gomme'),
    ('Milano', 'Mister Wash Milano Sempione', '02 34538910', 'Corso Sempione 88, Milano', 'TUNNEL/ALTA VELOCITÀ', 'Milano Sempione & Fiera', '~4 km dal centro', '390234538910', 'Tunnel 35 metri ad altissima frequenza, grandi lotti fusti monocomponente'),
    ('Milano', 'Detailing Milano Nord', '347 1829304', 'Via Privata De Vitalis 12, Milano Niguarda', 'DETAILING NANOTECH', 'Milano Nord', '~6 km dal centro', '393471829304', 'Centro detailing certificato, interesse per paste abrasive e sigillanti nanotech'),
    ('Milano', 'Autolavaggio Loreto Car Care', '328 4492019', 'Via Andrea Costa 8, Milano Loreto', 'MANO/INTERNI', 'Milano Loreto & Buenos Aires', '~3 km dal centro', '393284492019', 'Specializzato smacchiatura tappezzerie e dressing pelle'),
    ('Milano', 'Self Wash H24 San Siro', '02 48701923', 'Via Novara 110, Milano San Siro', 'SELF H24 PISTE', 'Milano Ovest', '~5 km dal centro', '390248701923', '6 piste alta pressione H24 con distributore, cera calda e schiuma attiva'),
    ('Milano', 'Sesto Wash Center', '02 2481920', 'Viale Gramsci 210, Sesto San Giovanni', 'PORTALE + SELF', 'Hinterland Nord (Sesto SG)', '~9 km da Milano', '39022481920', 'Impianto misto spazzole tessili e box lancia, ottimo per monocomponente'),
    ('Milano', 'Cinisello Car Detailing', '339 5182903', 'Via Lincoln 45, Cinisello Balsamo', 'DETAILING PRO', 'Hinterland Nord (Cinisello)', '~11 km da Milano', '393395182903', 'Lucidatura professionale carrozzerie e decontaminante cerchi'),
    ('Milano', 'Rho Fiera Express Wash', '02 9301822', 'Corso Europa 140, Rho', 'EXPRESS/FURGONI', 'Hinterland Ovest (Rho)', '~13 km da Milano', '39029301822', 'Lavaggio servito anche veicoli commerciali leggeri, sgrassatore alcalino'),
    ('Milano', 'Rozzano Clean Car', '02 8251930', 'Via Curiel 28, Rozzano', 'SERVITO/OZONO', 'Hinterland Sud (Rozzano)', '~10 km da Milano', '39028251930', 'Sanificazione interni all ozono e lavaggio completo'),
    ('Milano', 'San Donato Wash H24', '340 7712940', 'Via Emilia 15, San Donato Milanese', 'SELF H24/PORTALE', 'Hinterland Sud-Est (San Donato)', '~8 km da Milano', '393407712940', 'Stazione ad alto transito asse via Emilia, fornitura fusti continuativa'),
    ('Milano', 'Monza Road Car Care', '039 2028190', 'Viale Brianza 33, Monza', 'FLOTTE/SERVITO', 'Monza & Brianza', '~15 km da Milano', '390392028190', 'Convenzioni flotte e auto aziendali, detergenti cerchi e moscerini')
]

torino_leads = [
    ('Torino', 'Torino Wash Moncalieri', '011 6408910', 'Corso Savona 42, Moncalieri', 'PISTE SELF + CAMION', 'Torino Sud (Moncalieri)', '~7 km dal centro', '390116408910', 'Grandi piste lancia e lavaggio veicoli commerciali con spazzoloni'),
    ('Torino', 'Autolavaggio Spazio Torino Centro', '011 5621890', 'Corso Vittorio Emanuele II 92, Torino', 'A MANO/SERVITO', 'Torino Centro', '~1 km dal centro', '390115621890', 'Lavaggio accurato a mano centro città, shampoo profumato ed asciugatura pelle'),
    ('Torino', 'Eco Wash Lingotto', '345 8812903', 'Via Nizza 280, Torino Lingotto', 'VAPORE & DETAILING', 'Torino Lingotto', '~4 km dal centro', '393458812903', 'Lavaggio interno a vapore secco e trattamenti igienizzanti'),
    ('Torino', 'Rivoli Car Care', '011 9582019', 'Corso Francia 180, Rivoli', 'TUNNEL AUTOMATICO', 'Torino Ovest (Rivoli)', '~12 km dal centro', '390119582019', 'Tunnel ad alta capacità oraria, cera autosciugante e polish liquido'),
    ('Torino', 'Nichelino Self H24', '331 4920182', 'Via Cuneo 55, Nichelino', 'SELF H24', 'Torino Sud (Nichelino)', '~9 km dal centro', '393314920182', '5 piste con lancia schiuma colorata e aspiratori potenti'),
    ('Torino', 'Collegno Detailing Garage', '347 9901823', 'Corso Pastrengo 34, Collegno', 'DETAILING PRO', 'Torino Ovest (Collegno)', '~8 km dal centro', '393479901823', 'Applicazione coating ceramici e cura interni pelle/alcantara'),
    ('Torino', 'Venaria Express Wash', '011 4591029', 'Corso Garibaldi 88, Venaria Reale', 'PORTALE SPAZZOLE', 'Torino Nord (Venaria)', '~10 km dal centro', '390114591029', 'Impianto a spazzole morbide antigraffio con prelavaggio chimico'),
    ('Torino', 'Settimo Torinese Wash Park', '011 8002910', 'Via Milano 72, Settimo Torinese', 'PARCO SELF 8 PISTE', 'Torino Nord-Est (Settimo)', '~13 km dal centro', '390118002910', 'Grande stazione self con 8 piste e lavamoquette self-service'),
    ('Torino', 'Grugliasco Le Gru Car Wash', '011 7708192', 'Via Crea 10, Grugliasco', 'A MANO C. COMMERCIALE', 'Torino Ovest (Grugliasco)', '~7 km dal centro', '390117708192', 'Lavaggio durante la sosta shopping, sgrassanti rapidi e lucidanti'),
    ('Torino', 'San Paolo Car Wash', '320 6619204', 'Corso Trapani 45, Torino San Paolo', 'LAVAGGIO SEDILI/MANO', 'Torino San Paolo', '~3 km dal centro', '393206619204', 'Specialista lavaggio sedili e tessuti con estrattore a iniezione')
]

for city, name, phone, addr, ptype, zone, dist, wa, notes in milano_leads + torino_leads:
    c.execute('SELECT id FROM b2b_car_washes WHERE name = ? AND city = ?', (name, city))
    if not c.fetchone():
        c.execute('''
            INSERT INTO b2b_car_washes (city, name, phone, address, plant_type, zone, distance, whatsapp_link, notes, lead_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DA_CHIAMARE')
        ''', (city, name, phone, addr, ptype, zone, dist, wa, notes))

conn.commit()

c.execute('SELECT city, COUNT(*) FROM b2b_car_washes GROUP BY city')
for r in c.fetchall():
    print(f"City in DB: {r[0]} -> {r[1]} autolavaggi censiti")

conn.close()
