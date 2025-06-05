import mysql.connector
import gzip

# Configura la connessione al tuo database
conn = mysql.connector.connect(
    host="",
    user="",
    password="",
    database="",
    port=""
)

# Crea un cursore per eseguire comandi SQL
cursor = conn.cursor()

# Definisci il nome della tabella di origine e della tabella di destinazione
tabella_origine = "Analysis"
tabella_destinazione = "AnalysisResult"

# Esegui una query per selezionare le righe dalla tabella di origine in blocchi
batch_size = 50  # Definisci il numero di righe per batch
offset = 0

while True:
    print(f'done: {offset}')
    select_query = f"SELECT id, file_result FROM {tabella_origine} LIMIT {batch_size} OFFSET {offset};"
    cursor.execute(select_query)
    righe = cursor.fetchall()
    
    if not righe:
        break  # Interrompi il ciclo se non ci sono più righe da selezionare
    
    # Inserisci le righe nella tabella di destinazione
    for riga in righe:
        # Modifica le colonne in base alle tue esigenze
        # Ad esempio, supponiamo che tu voglia selezionare solo alcune colonne
        # e che ci siano differenze nei nomi delle colonne tra le tabelle
        id_versione = riga[0]
        file = riga[1]

        # Esegui compressione del file
        if file:
            file_compresso = gzip.compress(file, compresslevel=9, mtime=None)
            # Esegui l'operazione di inserimento nella tabella di destinazione
            insert_query = f"INSERT INTO {tabella_destinazione} (analysis_id, file_result) VALUES (%s, %s);"
            cursor.execute(insert_query, (id_versione, file_compresso))

            update_query = f"UPDATE {tabella_origine} SET file_result=NULL WHERE id={id_versione}"
            cursor.execute(update_query)

    # Esegui il commit della transazione per rendere permanenti le modifiche per questo batch
    conn.commit()
    
    offset += batch_size

# Chiudi la connessione al database
cursor.close()
conn.close()
