from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
import psycopg2
import os
import json
from datetime import datetime, timedelta

app = FastAPI()

# 🔓 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🔐 JWT Config
SECRET_KEY = "minha_chave_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔌 Conexão com PostgreSQL
def conectar():
    return psycopg2.connect(
        dbname="db_leis",
        user="postgres",
        password="Dl@$1958",
        host="localhost",
        port="5432"
    )

# 🔐 Utilitários
def verificar_senha(senha_plain, senha_hash):
    return pwd_context.verify(senha_plain, senha_hash)

def gerar_hash_senha(senha):
    return pwd_context.hash(senha)

def criar_token_acesso(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def obter_usuario(email: str):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, email, senha FROM usuarios WHERE email = %s;", (email,))
    resultado = cur.fetchone()
    cur.close()
    conn.close()
    if resultado:
        return {"id": resultado[0], "nome": resultado[1], "email": resultado[2], "senha": resultado[3]}
    return None

def autenticar_usuario(email: str, senha: str):
    usuario = obter_usuario(email)
    if usuario and verificar_senha(senha, usuario["senha"]):
        return usuario
    return None

async def obter_usuario_logado(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        usuario = obter_usuario(email)
        if usuario is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return usuario
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# 🔐 Login
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = autenticar_usuario(form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    token = criar_token_acesso({"sub": usuario["email"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}

# 🏠 Raiz
@app.get("/")
def home():
    return {"mensagem": "API de documentos está ativa!"}

# 📄 Listar documentos
@app.get("/documentos")
def listar_documentos(usuario: dict = Depends(obter_usuario_logado)):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.titulo, td.nome AS tipo, o.nome AS orgao, s.nome AS status, p.nome AS prioridade
        FROM documentos d
        LEFT JOIN tipos_documento td ON d.tipo_documento_id = td.id
        LEFT JOIN orgaos o ON d.orgao_id = o.id
        LEFT JOIN status s ON d.status_id = s.id
        LEFT JOIN prioridade p ON d.prioridade_id = p.id
        ORDER BY d.id;
    """)
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0],
            "titulo": r[1],
            "tipo": r[2],
            "orgao": r[3],
            "status": r[4],
            "prioridade": r[5]
        }
        for r in resultados
    ]

# 📤 Upload com validação
@app.post("/upload")
async def upload_documento(file: UploadFile = File(...), usuario: dict = Depends(obter_usuario_logado)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Apenas arquivos JSON são permitidos.")
    conteudo = await file.read()
    try:
        dados = json.loads(conteudo)
        titulo = dados.get("titulo")
        tipo = dados.get("tipo")
        orgao = dados.get("orgao")
        status = dados.get("status")
        prioridade = dados.get("prioridade")
        if not titulo or not tipo or not orgao:
            raise ValueError("Campos obrigatórios ausentes.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao validar conteúdo: {e}")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO documentos (titulo, tipo_documento_id, orgao_id, status_id, prioridade_id)
        VALUES (%s,
                (SELECT id FROM tipos_documento WHERE nome = %s),
                (SELECT id FROM orgaos WHERE nome = %s),
                (SELECT id FROM status WHERE nome = %s),
                (SELECT id FROM prioridade WHERE nome = %s));
    """, (titulo, tipo, orgao, status, prioridade))
    conn.commit()
    cur.close()
    conn.close()

    return {"mensagem": f"Documento '{titulo}' salvo no banco com sucesso."}

# 👥 Administração de usuários
@app.get("/usuarios")
def listar_usuarios(usuario: dict = Depends(obter_usuario_logado)):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, email FROM usuarios;")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": u[0], "nome": u[1], "email": u[2]} for u in usuarios]

@app.post("/usuarios")
def criar_usuario(nome: str = Form(...), email: str = Form(...), senha: str = Form(...)):
    senha_hash = gerar_hash_senha(senha)
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s);", (nome, email, senha_hash))
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensagem": "Usuário criado com sucesso"}