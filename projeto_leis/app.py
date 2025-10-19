import os
import psycopg2
from flask import Flask, render_template, request, jsonify, redirect
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis do arquivo .env

app = Flask(__name__)

def get_db_connection():
    """Estabelece a conexão com o banco de dados PostgreSQL."""
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    return conn

@app.route('/')
def index():
    """Serve a página principal (dashboard)."""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_documents():
    """API endpoint para buscar documentos."""
    data = request.get_json()
    search_query = data.get('query', '')
    filters = data.get('filters', {})

    conn = get_db_connection()
    cur = conn.cursor()

    sql = """
        SELECT
            d.id, d.titulo, d.ementa, d.numero, d.ano, d.data_publicacao,
            td.nome as tipo_nome, o.nome as orgao_nome,
            ts_headline('portuguese', d.ementa, to_tsquery('portuguese', %s), 'StartSel=<mark>, StopSel=</mark>') as ementa_destaque,
            ts_rank(to_tsvector('portuguese', d.conteudo_texto), to_tsquery('portuguese', %s)) as rank
        FROM documentos d
        JOIN tipos_documento td ON d.tipo_documento_id = td.id
        JOIN orgaos o ON d.orgao_id = o.id
        WHERE to_tsvector('portuguese', d.conteudo_texto) @@ to_tsquery('portuguese', %s)
    """
    
    params = [search_query, search_query, search_query]

    if filters.get('tipo'):
        sql += " AND d.tipo_documento_id = %s"
        params.append(filters['tipo'])
    
    if filters.get('orgao'):
        sql += " AND d.orgao_id = %s"
        params.append(filters['orgao'])

    if filters.get('ano'):
        sql += " AND d.ano = %s"
        params.append(filters['ano'])

    sql += " ORDER BY rank DESC, d.data_publicacao DESC LIMIT 50;"

    cur.execute(sql, params)
    results = cur.fetchall()
    
    documents = []
    for row in results:
        documents.append({
            "id": row[0], "titulo": row[1], "ementa": row[2],
            "numero": row[3], "ano": row[4], "data_publicacao": row[5].strftime('%d/%m/%Y'),
            "tipo": row[6], "orgao": row[7], "ementa_destaque": row[8]
        })

    cur.close()
    conn.close()
    
    return jsonify(documents)

@app.route('/api/filters')
def get_filters():
    """API endpoint para obter os valores dos filtros (tipos, órgãos, etc.)."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, nome FROM tipos_documento ORDER BY nome;")
    tipos = cur.fetchall()

    cur.execute("SELECT id, nome FROM orgaos ORDER BY nome;")
    orgaos = cur.fetchall()
    
    cur.execute("SELECT DISTINCT ano FROM documentos ORDER BY ano DESC;")
    anos = [row[0] for row in cur.fetchall() if row[0]]

    cur.close()
    conn.close()

    return jsonify({
        "tipos": [{"id": t[0], "nome": t[1]} for t in tipos],
        "orgaos": [{"id": o[0], "nome": o[1]} for o in orgaos],
        "anos": anos
    })

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """Rota para exibir e processar o formulário de cadastro de documentos."""
    if request.method == 'POST':
        titulo = request.form['titulo']
        ementa = request.form['ementa']
        numero = request.form['numero']
        ano = request.form['ano']
        data_publicacao = request.form['data_publicacao']
        tipo_documento_id = request.form['tipo_documento_id']
        orgao_id = request.form['orgao_id']
        conteudo_texto = request.form['conteudo_texto']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO documentos (
                titulo, ementa, numero, ano, data_publicacao,
                tipo_documento_id, orgao_id, conteudo_texto
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (titulo, ementa, numero, ano, data_publicacao, tipo_documento_id, orgao_id, conteudo_texto))
        conn.commit()
        cur.close()
        conn.close()
        return render_template("sucesso.html")

    return render_template("cadastrar.html")

if __name__ == '__main__':
    app.run(debug=True)