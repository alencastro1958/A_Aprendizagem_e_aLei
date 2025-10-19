import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Conexão com o banco
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cur = conn.cursor()

# Consulta os documentos
cur.execute("SELECT id, titulo, ementa FROM documentos ORDER BY id;")
documentos = cur.fetchall()

# Exibe os resultados
for doc in documentos:
    print(f"{doc[0]} | {doc[1]} | {doc[2][:80]}...")

cur.close()
conn.close()