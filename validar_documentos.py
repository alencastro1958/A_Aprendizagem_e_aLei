import psycopg2

# Conexão direta
def conectar():
    return psycopg2.connect(
        dbname="db_leis",
        user="postgres",
        password="Dl@$1958",
        host="localhost",
        port="5432",
        client_encoding='UTF8'
    )

conn = conectar()
cur = conn.cursor()

# 📘 Documentos por tipo
print("\n📘 Documentos por tipo:")
cur.execute("SELECT tipo_documento_id, COUNT(*) FROM documentos GROUP BY tipo_documento_id;")
for tipo, total in cur.fetchall():
    print(f"Tipo {tipo} → {total} documentos")

# 🏛️ Documentos por órgão
print("\n🏛️ Documentos por órgão:")
cur.execute("SELECT orgao_id, COUNT(*) FROM documentos GROUP BY orgao_id;")
for orgao, total in cur.fetchall():
    print(f"Órgão {orgao} → {total} documentos")

# 📅 Documentos por ano
print("\n📅 Documentos por ano:")
cur.execute("SELECT ano, COUNT(*) FROM documentos GROUP BY ano ORDER BY ano;")
for ano, total in cur.fetchall():
    print(f"Ano {ano} → {total} documentos")

cur.close()
conn.close()