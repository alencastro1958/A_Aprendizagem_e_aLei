from PyPDF2 import PdfReader
import os

def limpar_texto(texto):
    if isinstance(texto, bytes):
        return texto.decode("utf-8", errors="ignore")
    return str(texto).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

PASTA = "documentos"

for arquivo in os.listdir(PASTA):
    if arquivo.lower().endswith(".pdf"):
        caminho = os.path.join(PASTA, arquivo)
        try:
            reader = PdfReader(caminho)
            texto = "\n".join(page.extract_text() or "" for page in reader.pages)
            texto_limpo = limpar_texto(texto)
            print(f"✅ Texto limpo de: {arquivo}")
        except Exception as e:
            print(f"❌ Erro ao extrair de {arquivo}: {e}")