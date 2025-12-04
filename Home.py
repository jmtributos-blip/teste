import streamlit as st

st.set_page_config(
    page_title="Minha Aplicação Fiscal",
    page_icon="📊",
    layout="wide"
)

st.title("Bem-vindo à Aplicação de Análise Fiscal!")
st.markdown("""
    Selecione uma das opções no menu lateral para começar:
    - **Visualizador NFSe:** Analise suas Notas Fiscais de Serviço Eletrônicas e confira retenções.
    - **Divisão de Sócios:** (Em construção) Gerencie a divisão de lucros entre sócios.
""")

st.info("Utilize a barra lateral à esquerda para navegar entre as seções da aplicação.")

# Você pode adicionar mais conteúdo ou links aqui se desejar