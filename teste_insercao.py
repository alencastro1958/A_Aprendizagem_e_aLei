import os
import psycopg2
from PyPDF2 import PdfReader
import re

# ✅ Conexão direta sem dotenv
def conectar():
    return psycopg2.connect(
        dbname="db_leis",
        user="postgres",
        password="Dl@$1958",  # substitua se necessário
        host="localhost",
        port="5432",
        client_encoding='UTF8'
    )

# Função para limpar texto e garantir codificação UTF-8 segura
def limpar_texto(texto):
    if isinstance(texto, bytes):
        return texto.decode("utf-8", errors="ignore")
    return str(texto).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

# Extrai texto de PDF
def extrair_texto_pdf(caminho):
    try:
        reader = PdfReader(caminho)
        texto = ""
        for page in reader.pages:
            raw = page.extract_text()
            if raw:
                texto += raw
        return texto
    except Exception as e:
        print(f"Erro ao ler PDF: {e}")
        return ""

# Extrai metadados simples
def extrair_metadados(texto):
    try:
        titulo = re.search(r"(Portaria|Decreto|Lei)[^\n]{0,100}", texto)
        numero = re.search(r"n[ºo]?\s*(\d{3,6})", texto)
        ano = re.search(r"\b(20\d{2}|19\d{2})\b", texto)
        data = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", texto)

        return {
            "titulo": titulo.group(0) if titulo else "Documento sem título",
            "numero": numero.group(1) if numero else "0000",
            "ano": int(ano.group(1)) if ano else 2025,
            "data_publicacao": data.group(1).replace("/", "-") if data else "2025-01-01",
            "ementa": texto[:300].strip().replace("\n", " "),
            "conteudo_texto": texto
        }
    except Exception as e:
        print(f"Erro ao extrair metadados: {e}")
        return {
            "titulo": "Documento sem título",
            "numero": "0000",
            "ano": 2025,
            "data_publicacao": "2025-01-01",
            "ementa": texto[:300].strip().replace("\n", " "),
            "conteudo_texto": texto
        }

# Insere no banco com log detalhado
def inserir_documento(doc):
    try:
        conn = conectar()
        cur = conn.cursor()

        def limpar(valor):
            return str(valor).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

        titulo = limpar(doc["titulo"])
        ementa = limpar(doc["ementa"])
        numero = limpar(doc["numero"])
        conteudo = limpar(doc["conteudo_texto"])

        print("\n🔍 Tentando inserir:")
        print(f"Título: {titulo}")
        print(f"Ementa: {ementa[:80]}...")
        print(f"Número: {numero}")
        print(f"Ano: {doc['ano']}")
        print(f"Data: {doc['data_publicacao']}")
        print(f"Conteúdo (início): {conteudo[:80]}...")

        cur.execute("""
            INSERT INTO documentos (
                titulo, ementa, numero, ano, data_publicacao,
                tipo_documento_id, orgao_id, conteudo_texto
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            titulo,
            ementa,
            numero,
            doc["ano"],
            doc["data_publicacao"],
            1,
            1,
            conteudo
        ))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Inserido: {titulo}")
    except Exception as e:
        print(f"❌ Erro ao inserir: {doc['titulo']} → {e}")

# Testa os PDFs
PASTA = "documentos"
for arquivo in os.listdir(PASTA):
    if arquivo.lower().endswith(".pdf"):
        caminho = os.path.join(PASTA, arquivo)
        texto = limpar_texto(extrair_texto_pdf(caminho))
        if texto.strip():
            doc = extrair_metadados(texto)
            inserir_documento(doc)