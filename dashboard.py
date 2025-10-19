import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

# 🔐 Login com JWT
def autenticar():
    st.sidebar.title("🔐 Login")
    email = st.sidebar.text_input("Email")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        resposta = requests.post("http://127.0.0.1:8888/token", data={"username": email, "password": senha})
        if resposta.status_code == 200:
            token = resposta.json()["access_token"]
            st.session_state["token"] = token
            st.success("Login realizado com sucesso!")
        else:
            st.error("Credenciais inválidas")

if "token" not in st.session_state:
    autenticar()
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

st.set_page_config(page_title="Painel de Documentos Legislativos", layout="wide")
st.title("📘 Painel de Documentos Legislativos")

# 🔄 Carregar dados da API
@st.cache_data
def carregar_dados():
    try:
        resposta = requests.get("http://127.0.0.1:8888/documentos", headers=headers)
        resposta.raise_for_status()
        return pd.DataFrame(resposta.json())
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados()

# 🎛️ Filtros
col1, col2 = st.columns(2)
tipos = df["tipo"].dropna().unique()
orgaos = df["orgao"].dropna().unique()
status = df["status"].dropna().unique()
prioridades = df["prioridade"].dropna().unique()

with col1:
    tipo_selecionado = st.multiselect("Filtrar por Tipo", tipos)
    orgao_selecionado = st.multiselect("Filtrar por Órgão", orgaos)

with col2:
    status_selecionado = st.multiselect("Filtrar por Status", status)
    prioridade_selecionada = st.multiselect("Filtrar por Prioridade", prioridades)

# 🧮 Aplicar filtros
filtro = df.copy()
if tipo_selecionado:
    filtro = filtro[filtro["tipo"].isin(tipo_selecionado)]
if orgao_selecionado:
    filtro = filtro[filtro["orgao"].isin(orgao_selecionado)]
if status_selecionado:
    filtro = filtro[filtro["status"].isin(status_selecionado)]
if prioridade_selecionada:
    filtro = filtro[filtro["prioridade"].isin(prioridade_selecionada)]

# 📋 Tabela
st.subheader("📄 Documentos Filtrados")
st.dataframe(filtro, use_container_width=True)

# 📥 Exportar CSV
st.download_button(
    label="📥 Exportar dados filtrados para CSV",
    data=filtro.to_csv(index=False).encode("utf-8"),
    file_name="documentos_filtrados.csv",
    mime="text/csv"
)

# 📘 Gráfico por tipo
if not filtro.empty and "tipo" in filtro.columns:
    st.subheader("📘 Distribuição por Tipo de Documento")
    grafico_tipo = px.histogram(filtro, x="tipo", title="Documentos por Tipo")
    st.plotly_chart(grafico_tipo, use_container_width=True)

# 🏛️ Gráfico por órgão
if not filtro.empty and "orgao" in filtro.columns:
    st.subheader("🏛️ Distribuição por Órgão")
    grafico_orgao = px.histogram(filtro, x="orgao", title="Documentos por Órgão")
    st.plotly_chart(grafico_orgao, use_container_width=True)

# 📤 Upload de Documento JSON
st.subheader("📤 Upload de Documento JSON para API")
arquivo = st.file_uploader("Escolha um arquivo JSON", type=["json"])

if arquivo:
    try:
        dados = json.load(arquivo)
        st.json(dados)
        files = {"file": (arquivo.name, json.dumps(dados))}
        resposta = requests.post("http://127.0.0.1:8888/upload", headers=headers, files=files)
        if resposta.status_code == 200:
            st.success(resposta.json()["mensagem"])
        else:
            st.error("Erro ao enviar o arquivo para a API.")
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

# 👥 Administração de Usuários
st.subheader("👥 Painel de Administração de Usuários")

with st.expander("📋 Listar Usuários"):
    resposta = requests.get("http://127.0.0.1:8888/usuarios", headers=headers)
    if resposta.status_code == 200:
        usuarios = pd.DataFrame(resposta.json())
        st.dataframe(usuarios)
    else:
        st.error("Erro ao carregar usuários.")

with st.expander("➕ Criar Novo Usuário"):
    nome = st.text_input("Nome")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Criar Usuário"):
        resposta = requests.post(
            "http://127.0.0.1:8888/usuarios",
            headers=headers,
            data={"nome": nome, "email": email, "senha": senha}
        )
        if resposta.status_code == 200:
            st.success("Usuário criado com sucesso!")
        else:
            st.error(resposta.json()["detail"])
                