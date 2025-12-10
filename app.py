import os
import datetime
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit as st

# ====== CONFIGURAÇÕES INICIAIS DO BANCO DE DADOS ======
db_path = "database.db"
engine = create_engine(f"sqlite:///{db_path}")
Base = declarative_base()

# Modelo/Table: NFSe
class NFSe(Base):
    __tablename__ = "nfses"
    id = Column(Integer, primary_key=True)
    cliente = Column(String(255), nullable=False)
    data_envio = Column(String(50), nullable=False)
    arquivo_xml = Column(Text, nullable=False)  # XML salvo como texto puro

# Criar o banco e as tabelas (se ainda não existirem)
if not os.path.exists(db_path):
    Base.metadata.create_all(engine)

# Configurar conexão com o banco e inicializar a sessão
Session = sessionmaker(bind=engine)
session = Session()

# ====== FUNÇÕES DA APLICAÇÃO ======

# Função: Upload de XML e Salvamento no Banco de Dados
def upload_xml():
    """Permite que o usuário envie arquivos XML e salve no banco de dados."""
    st.subheader("Envie seu XML")
    arquivo = st.file_uploader("Selecione um arquivo XML:", type=["xml"])

    if arquivo:
        try:
            xml_content = arquivo.read().decode("utf-8")  # Lê o conteúdo do XML
            cliente = st.text_input("Informe o nome do cliente:")

            if cliente and st.button("Salvar XML"):
                # Salvar os dados no banco de dados
                data_envio = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Data de envio
                novo_registro = NFSe(cliente=cliente, data_envio=data_envio, arquivo_xml=xml_content)

                session.add(novo_registro)
                session.commit()

                st.success(f"XML do cliente '{cliente}' salvo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

# Função: Exibir e Baixar Registros do Banco de Dados
def listar_registros():
    """Exibe todos os registros no banco de dados e permite visualizar/baixar XMLs."""
    st.subheader("NFS-e Registradas no Banco de Dados")

    registros = session.query(NFSe).all()  # Busca todos os registros do banco

    if not registros:
        st.info("Nenhuma NFS-e encontrada.")
    else:
        for registro in registros:
            st.subheader(f"NFS-e ID: {registro.id} | Cliente: {registro.cliente}")
            st.text(f"Data de Envio: {registro.data_envio}")

            # Botão para visualizar o conteúdo do XML
            if st.button(f"Visualizar XML ({registro.id})", key=f"ver-{registro.id}"):
                st.code(registro.arquivo_xml, language="xml")

            # Botão para download do XML
            st.download_button(
                label="Baixar XML",
                data=registro.arquivo_xml.encode("utf-8"),
                file_name=f"{registro.cliente}_nfse_{registro.id}.xml",
                mime="application/xml"
            )

# Função: Buscar Registros pelo ID ou Nome do Cliente
def buscar_registro():
    """Permite buscar NFS-e pelo ID ou nome do cliente."""
    st.subheader("Buscar Registros")
    busca_input = st.text_input("Informe o ID ou Nome do Cliente para buscar:")

    if st.button("Buscar"):
        if busca_input.isdigit():
            # Busca por ID
            resultados = session.query(NFSe).filter(NFSe.id == int(busca_input)).all()
        else:
            # Busca por Nome
            resultados = session.query(NFSe).filter(NFSe.cliente.ilike(f"%{busca_input}%")).all()

        if resultados:
            for registro in resultados:
                st.write(f"**ID:** {registro.id} | **Cliente:** {registro.cliente}")
                st.code(registro.arquivo_xml, language="xml")
        else:
            st.warning("Nenhum registro encontrado para a busca realizada.")

# Função: Exibir os Registros em uma Tabela no Streamlit
def exibir_tabela():
    """Exibe os registros completos como uma tabela dentro do Streamlit."""
    st.subheader("Visualizar Tabela Completa de Registros")

    registros = session.query(NFSe).all()  # Buscar registros
    if not registros:
        st.info("Nenhuma NFS-e registrada no banco de dados.")
    else:
        # Transformar os registros em DataFrame
        dados = [{
            "ID": registro.id,
            "Cliente": registro.cliente,
            "Data de Envio": registro.data_envio,
        } for registro in registros]

        df = pd.DataFrame(dados)
        st.dataframe(df)

# ====== INTERFACE DO USUÁRIO ======

st.title("Gerenciador de NFS-e")
st.sidebar.title("Menu")
# Menu lateral com as opções
menu = st.sidebar.selectbox(
    "Escolha uma opção", 
    ["Enviar XML", "Listar Registros", "Buscar Registro", "Visualizar Tabela"]
)

if menu == "Enviar XML":
    upload_xml()
elif menu == "Listar Registros":
    listar_registros()
elif menu == "Buscar Registro":
    buscar_registro()
elif menu == "Visualizar Tabela":
    exibir_tabela()
