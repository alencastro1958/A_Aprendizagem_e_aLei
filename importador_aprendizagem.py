import os
import re
import psycopg2
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import pandas as pd

load_dotenv()

# Conexão com o banco
def conectar():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
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

# Extrai texto de DOCX
def extrair_texto_docx(caminho):
    try:
        doc = Document(caminho)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"Erro ao ler DOCX: {e}")
        return ""

# Extrai texto de imagem com OCR
def extrair_texto_imagem(caminho):
    try:
        img = Image.open(caminho)
        return pytesseract.image_to_string(img, lang='por')
    except Exception as e:
        print(f"Erro ao ler imagem: {e}")
        return ""

# Extrai texto de XLSX
def extrair_texto_xlsx(caminho):
    try:
        df = pd.read_excel(caminho)
        return df.to_string(index=False)
    except Exception as e:
        print(f"Erro ao ler XLSX: {e}")
        return ""

# Extrai metadados simples
def extrair_metadados(texto):
    try:
        titulo = re.search(r"(Portaria|Decreto|Lei|Instrução Normativa|Resolução|Manual)[^\n]{0,100}", texto)
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

# Insere no banco
def inserir_documento(doc, tipo_id=1, orgao_id=1):
    try:
        conn = conectar()
        cur = conn.cursor()

        # Limpeza completa dos campos
        def limpar(valor):
            return str(valor).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

        cur.execute("""
            INSERT INTO documentos (
                titulo, ementa, numero, ano, data_publicacao,
                tipo_documento_id, orgao_id, conteudo_texto
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            limpar(doc["titulo"]),
            limpar(doc["ementa"]),
            limpar(doc["numero"]),
            doc["ano"],
            doc["data_publicacao"],
            tipo_id,
            orgao_id,
            limpar(doc["conteudo_texto"])
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao inserir no banco: {e}")

# Caminho da pasta com documentos
PASTA = "documentos"

# Processa todos os arquivos
for arquivo in os.listdir(PASTA):
    caminho = os.path.join(PASTA, arquivo)
    texto = ""

    try:
        if arquivo.lower().endswith(".pdf"):
            texto = extrair_texto_pdf(caminho)
        elif arquivo.lower().endswith(".docx"):
            texto = extrair_texto_docx(caminho)
        elif arquivo.lower().endswith((".jpeg", ".jpg", ".png")):
            texto = extrair_texto_imagem(caminho)
        elif arquivo.lower().endswith(".xlsx"):
            texto = extrair_texto_xlsx(caminho)
        else:
            print(f"❌ Tipo de arquivo não suportado: {arquivo}")
            continue

        # ✅ Aplica limpeza após extração
        texto = limpar_texto(texto)

        if texto.strip():
            doc = extrair_metadados(texto)
            inserir_documento(doc)
            print(f"✅ Inserido: {doc['titulo']}")
        else:
            print(f"⚠️ Nenhum texto extraído de: {arquivo}")

    except Exception as e:
        print(f"⚠️ Erro ao processar {arquivo}: {e}")