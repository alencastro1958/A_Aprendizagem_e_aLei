import os
import re
import psycopg2
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

load_dotenv()

def conectar():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        client_encoding='UTF8'
    )

def extrair_texto_pdf(caminho):
    reader = PdfReader(caminho)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def extrair_texto_docx(caminho):
    doc = Document(caminho)
    return "\n".join(p.text for p in doc.paragraphs)

def extrair_metadados(texto):
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

def testar_insercao(doc):
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT 1")  # Testa conexão

        # Testa cada campo individualmente
        for campo, valor in doc.items():
            try:
                str(valor).encode("utf-8")
            except Exception as e:
                print(f"❌ Erro no campo '{campo}' do documento '{doc['titulo']}': {e}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro geral: {e}")

PASTA = "documentos"

for arquivo in os.listdir(PASTA):
    caminho = os.path.join(PASTA, arquivo)
    if arquivo.lower().endswith(".pdf"):
        texto = extrair_texto_pdf(caminho)
    elif arquivo.lower().endswith(".docx"):
        texto = extrair_texto_docx(caminho)
    else:
        continue

    doc = extrair_metadados(texto)
    testar_insercao(doc)