import pandas as pd
import sqlite3
import os

os.makedirs("data/db", exist_ok=True)

db = "data/db/database.sqlite"
csv = "data/cleaned/cleaned_file.csv"
DROP_STAGING_AFTER = True  

staging_df = pd.read_csv(csv, sep='\t')
staging_df = staging_df.reset_index(drop=True)
staging_df['row_id'] = staging_df.index + 1  

conn = sqlite3.connect(db)
cur = conn.cursor()

staging_df.to_sql("StagingTable", conn, if_exists="replace", index=False)

cur.execute('''
CREATE TABLE IF NOT EXISTS Soidukid (
    soiduki_id INTEGER PRIMARY KEY,
    mark TEXT,
    mudel TEXT,
    esmane_reg_aasta INTEGER,
    kategooria TEXT,
    keretyyp TEXT
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Tehnoylevaatuspunktid (
    punkti_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nimi TEXT,
    punkti_kood TEXT
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Tootajad (
    tootaja_id INTEGER PRIMARY KEY
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS TehnoylevaatuspunktiTootajad (
    punkti_tootaja_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tootaja_id INTEGER,
    punkti_id INTEGER,
    FOREIGN KEY (tootaja_id) REFERENCES Tootajad(tootaja_id),
    FOREIGN KEY (punkti_id) REFERENCES Tehnoylevaatuspunktid(punkti_id)
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Ylevaatused (
    ylevaatuse_id INTEGER PRIMARY KEY AUTOINCREMENT,
    punkti_tootaja_id INTEGER,
    soiduki_id INTEGER,
    otsus TEXT,
    kuupaev DATE,
    liik TEXT,
    FOREIGN KEY (punkti_tootaja_id) REFERENCES TehnoylevaatuspunktiTootajad(punkti_tootaja_id),
    FOREIGN KEY (soiduki_id) REFERENCES Soidukid(soiduki_id)
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Rikked (
    rikke_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rikke_kood TEXT
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS YlevaatuseRikked (
    ylevaatuse_rikke_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rikke_id INTEGER,
    ylevaatuse_id INTEGER,
    FOREIGN KEY (rikke_id) REFERENCES Rikked(rikke_id),
    FOREIGN KEY (ylevaatuse_id) REFERENCES Ylevaatused(ylevaatuse_id)
)
''')
conn.commit()

cur.execute('''
INSERT OR IGNORE INTO Soidukid (soiduki_id, mark, mudel, esmane_reg_aasta, kategooria, keretyyp)
SELECT DISTINCT SOIDUK_ID, MARK, MUDEL, ESMANE_REG_AASTA, KATEGOORIA, KERETYYP
FROM StagingTable
''')

cur.execute('''
INSERT OR IGNORE INTO Tehnoylevaatuspunktid (nimi, punkti_kood)
SELECT DISTINCT TEHNOYLEVAATUSPUNKT, PUNKTI_KOOD
FROM StagingTable
''')

cur.execute('''
INSERT OR IGNORE INTO Tootajad (tootaja_id)
SELECT DISTINCT TOOTAJA
FROM StagingTable
''')

cur.execute('''
INSERT OR IGNORE INTO TehnoylevaatuspunktiTootajad (tootaja_id, punkti_id)
SELECT DISTINCT t.tootaja_id, p.punkti_id
FROM StagingTable s
JOIN Tehnoylevaatuspunktid p ON s.PUNKTI_KOOD = p.punkti_kood
JOIN Tootajad t ON s.TOOTAJA = t.tootaja_id
''')
conn.commit()

cur.execute('''
INSERT OR IGNORE INTO Ylevaatused (punkti_tootaja_id, soiduki_id, otsus, kuupaev, liik)
SELECT DISTINCT ttp.punkti_tootaja_id, s.SOIDUK_ID, s.YLEVAATUSOTSUS, s.YV_KUUPAEV, s.YLEVAATUSLIIK
FROM StagingTable s
JOIN TehnoylevaatuspunktiTootajad ttp 
ON s.TOOTAJA = ttp.tootaja_id  
JOIN Tehnoylevaatuspunktid tp 
ON s.PUNKTI_KOOD = tp.punkti_kood
WHERE ttp.punkti_id = tp.punkti_id
''')
conn.commit()

cur.execute('DROP TABLE IF EXISTS StagingToYlevaatus')
cur.execute('''
CREATE TEMP TABLE StagingToYlevaatus AS
SELECT s.row_id, y.ylevaatuse_id
FROM StagingTable s
JOIN Tehnoylevaatuspunktid p ON s.PUNKTI_KOOD = p.punkti_kood
JOIN TehnoylevaatuspunktiTootajad ttp 
ON s.TOOTAJA = ttp.tootaja_id 
AND ttp.punkti_id = p.punkti_id
JOIN Ylevaatused y
ON y.soiduki_id = s.SOIDUK_ID
AND y.kuupaev = s.YV_KUUPAEV
AND y.punkti_tootaja_id = ttp.punkti_tootaja_id;
''')
conn.commit()

rikked_expanded = staging_df[['row_id','RIKKED']].dropna(subset=['RIKKED']).copy()
rikked_expanded = rikked_expanded.assign(RIKKE=rikked_expanded['RIKKED'].str.split(';')).explode('RIKKE')
rikked_expanded['RIKKE'] = rikked_expanded['RIKKE'].str.strip()

rikked_unique = rikked_expanded[['RIKKE']].drop_duplicates().rename(columns={'RIKKE':'rikke_kood'})
rikked_unique.to_sql('Rikked', conn, if_exists='append', index=False)

rikked_sql = pd.read_sql("SELECT * FROM Rikked", conn)
staging_map = pd.read_sql("SELECT * FROM StagingToYlevaatus", conn)

yr_df = rikked_expanded.merge(staging_map, on='row_id', how='left')
yr_df = yr_df.merge(rikked_sql, left_on='RIKKE', right_on='rikke_kood', how='left')

yr_df = yr_df[['rikke_id','ylevaatuse_id']].drop_duplicates()
yr_df.to_sql('YlevaatuseRikked', conn, if_exists='append', index=False)

if DROP_STAGING_AFTER:
    cur.execute("DROP TABLE IF EXISTS StagingTable")
    
cur.execute('''
DELETE FROM YlevaatuseRikked
WHERE ylevaatuse_id IS NULL;
''')

conn.commit()
conn.close()