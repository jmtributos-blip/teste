import os

# Caminho onde o banco deveria estar
db_path = "database.db"

# Verificar se o arquivo existe
if os.path.exists(db_path):
    print(f"Banco encontrado: {db_path}")
else:
    print("Banco de dados NÃO encontrado!")




# app_viewer.py - REESCRITO COM DASHBOARD DE CONFERÊNCIA DE RETENÇÕES E ANÁLISE DE SEQUÊNCIA DE NF

import streamlit as st
import pandas as pd
import os
import tempfile
import numpy as np
import io # Importado para manipulação de bytes para download de Excel
import json # Para gerar o JSON do Plotly

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


# Importa a função de extração do seu nfse_parser
from nfse_parser import extract_nfse_data

# --- Configurações de Alíquotas e Limites de Retenção ---
# Para Lucro Presumido - Regime Normal (ajuste conforme a legislação vigente e o tipo de serviço)
# IMPORTANTE: Estas alíquotas e limites são referenciais e devem ser validadas pela equipe fiscal.
ALIQUOTA_IRRF = 0.015
LIMITE_IRRF_SERVICO = 666.67 # Valor do serviço para que haja retenção de IRRF

ALIQUOTA_CSLL = 0.01
ALIQUOTA_PIS = 0.0065
ALIQUOTA_COFINS = 0.03
LIMITE_CSRF_SERVICO = 215.05 # Valor do serviço para que haja retenção combinada (CSLL, PIS, COFINS)

# ISSQN é variável por município. A alíquota padrão abaixo é apenas um exemplo.
# Para uma conferência precisa de ISSQN, seria necessário uma base de dados de alíquotas por município.
ALIQUOTA_ISSQN_REFERENCIA = 0.03 # Alíquota de referência para cálculo de ISSQN esperado, se aplicável
# --- Configurações de Alíquotas para EQUIPARAÇÃO HOSPITALAR ---
# Baseado em Faturamento Bruto (Valor dos Serviços)
ALIQUOTA_IRPJ_EQ_HOSP = 0.012   # 1.2% do faturamento
ALIQUOTA_CSLL_EQ_HOSP = 0.0108  # 1.08% do faturamento
ALIQUOTA_PIS_EQ_HOSP = 0.0065   # 0.65% do faturamento
ALIQUOTA_COFINS_EQ_HOSP = 0.03  # 3.00% do faturamento
ALIQUOTA_ISSQN_EQ_HOSP = 0.0201 # 2.01% do faturamento
# --- Mapeamento de Nomes de Colunas para Exibição Amigável ---
# Mantenha os nomes originais como chaves para que o rename funcione corretamente.
column_display_names = {
    # NFSe Geral
    'Nfse.Id': 'ID NFSe',
    'Numero': 'Número da NF',
    'CodigoVerificacao': 'Código Verificação',
    'DataEmissao': 'Data Emissão',
    'NaturezaOperacao': 'Natureza Operação',
    'RegimeEspecialTributacao': 'Regime Tributação',
    'OptanteSimplesNacional': 'Simples Nacional',
    'IncentivadorCultural': 'Incentivador Cultural',

    # Serviço
    'DescricaoServico': 'Descrição do Serviço',
    'ItemListaServico': 'Item Lista Serviço',
    'CodigoTributacaoMunicipio': 'Cód. Tributação Município',
    'CodigoMunicipioServico': 'Cód. Município Serviço',

    # Valores do Serviço
    'ValorServicos': 'Valor dos Serviços',
    'ValorDeducoes': 'Deduções',
    'ValorPis': 'PIS',
    'ValorCofins': 'COFINS',
    'ValorInss': 'INSS',
    'ValorIr': 'IR',
    'ValorCsll': 'CSLL',
    'IssRetido': 'ISS Retido (Cód)',
    'ValorIss': 'Valor ISS',
    'ValorIssRetido': 'Valor ISS Retido',
    'OutrasRetencoes': 'Outras Retenções',
    'BaseCalculo': 'Base de Cálculo',
    'Aliquota': 'Alíquota',
    'ValorLiquidoNfse': 'Valor Líquido NFSe',
    'DescontoIncondicionado': 'Desconto Incondicionado',
    'DescontoCondicionado': 'Desconto Condicionado',

    # Prestador
    'Prestador.CpfCnpj': 'Prestador CNPJ',
    'Prestador.InscricaoMunicipal': 'Prestador Inscr. Municipal',
    'Prestador.RazaoSocial': 'Prestador Razão Social',
    'Prestador.Endereco.Logradouro': 'Prestador Logradouro',
    'Prestador.Endereco.Numero': 'Prestador Número',
    'Prestador.Endereco.Complemento': 'Prestador Complemento',
    'Prestador.Endereco.Bairro': 'Prestador Bairro',
    'Prestador.Endereco.CodigoMunicipio': 'Prestador Cód. Município',
    'Prestador.Endereco.Uf': 'Prestador UF',
    'Prestador.Endereco.Cep': 'Prestador CEP',
    'Prestador.Contato.Telefone': 'Prestador Telefone',
    'Prestador.Contato.Email': 'Prestador E-mail',

    # Tomador
    'TomadorServico.CpfCnpj': 'Tomador CNPJ/CPF',
    'TomadorServico.RazaoSocial': 'Tomador Razão Social',
    'TomadorServico.Endereco.Logradouro': 'Tomador Logradouro',
    'TomadorServico.Endereco.Numero': 'Tomador Número',
    'TomadorServico.Endereco.Bairro': 'Tomador Bairro',
    'TomadorServico.Endereco.CodigoMunicipio': 'Tomador Cód. Município',
    'TomadorServico.Endereco.Uf': 'Tomador UF',
    'TomadorServico.Endereco.Cep': 'Tomador CEP',
    'TomadorServico.Contato.Telefone': 'Tomador Telefone',

    # Órgão Gerador
    'OrgaoGerador.CodigoMunicipio': 'Org. Gerador Cód. Município',
    'OrgaoGerador.Uf': 'Org. Gerador UF',

    # Novas colunas calculadas/ajustadas para display
    'Competencia': 'Competência',
    'Tomador Tipo': 'Tomador Tipo',
    'Prestador Regime': 'Prestador Regime',
    'IsCancelled': 'Status Cancelamento',

    # Novas colunas para conferência de retenções (internas, não exibidas por padrão na tabela)
    'IR Esperado': 'IR Esperado',
    'CSLL Esperado': 'CSLL Esperado',
    'PIS Esperado': 'PIS Esperado',
    'COFINS Esperado': 'COFINS Esperado',
    'ISSQN Esperado': 'ISSQN Esperado',
    'Status IR': 'Status IR',
    'Status CSLL': 'Status CSLL',
    'Status PIS': 'Status PIS',
    'Status COFINS': 'Status COFINS',
    'Status ISS Retido': 'Status ISS Retido',
    'Status Geral Retenções': 'Status Geral Retenções'
}

# Colunas padrão a serem exibidas na tabela. As colunas de status e esperados NÃO estão aqui por padrão.
default_cols_to_show_initial = [
    'Data Emissão', 'Competência', 'Número da NF', 'Tomador Razão Social',
    'Valor dos Serviços', 'IR', 'CSLL', 'PIS', 'COFINS', 'Valor ISS Retido', 'Status Cancelamento'
]

# INÍCIO DA CORREÇÃO: Definição GLOBAL da lista de colunas monetárias
# Linha 95
currency_cols_for_display = [
    'Valor dos Serviços', 'Deduções', 'PIS', 'COFINS', 'INSS',
    'IR', 'CSLL', 'Valor ISS', 'Valor ISS Retido', 'Outras Retenções',
    'BaseCalculo', 'ValorLiquidoNfse', 'DescontoIncondicionado', 'DescontoCondicionado',
    'IR Esperado', 'CSLL Esperado', 'PIS Esperado', 'COFINS Esperado', 'ISSQN Esperado'
]
# FIM DA CORREÇÃO


# --- Configurações Iniciais da Página ---
st.set_page_config(
    page_title="NFSe XML Viewer - Fechamento Fiscal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("NFSe XML Viewer para Fechamento Fiscal")
st.markdown("Ferramenta para auxiliar a equipe do departamento fiscal na conferência de NFSe e cálculo de tributos.")

# --- Inicialização do Session State ---
if 'log_messages_viewer' not in st.session_state:
    st.session_state.log_messages_viewer = []
if 'df_processed_viewer' not in st.session_state:
    st.session_state.df_processed_viewer = None
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = default_cols_to_show_initial.copy()
if 'column_config' not in st.session_state:
    st.session_state.column_config = {}
if 'diagnosis_messages' not in st.session_state:
    st.session_state.diagnosis_messages = []
# NOVO: Inicializa a variável para armazenar os problemas de sequência
# Linha 120
if 'sequence_issues' not in st.session_state:
    st.session_state.sequence_issues = pd.DataFrame() # DataFrame vazio inicialmente
# FIM NOVO


# --- Função de Log ---
def log_message_viewer(message, level="info"):
    """Adiciona uma mensagem ao log na interface do Streamlit para o viewer."""
    st.session_state.log_messages_viewer.append((message, level))
    # Para garantir que as mensagens de log apareçam na barra lateral, mesmo que o container principal não exista
    # ou não esteja sendo exibido imediatamente.
    # É uma pequena adaptação pois `log_container_viewer` só é definido mais abaixo.
    # Em um ambiente de produção, esta função de log seria mais elaborada.
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    elif level == "success":
        st.success(message)
    else:
        # Se log_container_viewer estiver disponível, usa-o. Caso contrário, apenas printa.
        try:
            log_container_viewer.info(message)
        except NameError:
            pass # log_container_viewer not yet defined


# --- Funções Auxiliares para Cálculo de Retenções Esperadas ---
def calcular_irrf_esperado(valor_servicos):
    """Calcula o IRRF esperado para Lucro Presumido (Normal)."""
    if valor_servicos >= LIMITE_IRRF_SERVICO:
        return valor_servicos * ALIQUOTA_IRRF
    return 0.0

def calcular_csrf_esperado(valor_servicos):
    """Calcula CSLL, PIS e COFINS esperados para Lucro Presumido (Normal)."""
    if valor_servicos >= LIMITE_CSRF_SERVICO:
        return {
            'CSLL': valor_servicos * ALIQUOTA_CSLL,
            'PIS': valor_servicos * ALIQUOTA_PIS,
            'COFINS': valor_servicos * ALIQUOTA_COFINS
        }
    return {'CSLL': 0.0, 'PIS': 0.0, 'COFINS': 0.0}

def calcular_issqn_esperado(base_calculo, aliquota_xml):
    """
    Calcula o ISSQN esperado. Se a alíquota do XML for válida, usa-a.
    Caso contrário, usa uma alíquota de referência definida nas constantes.
    """
    if base_calculo is None or base_calculo <= 0:
        return 0.0
    # Alíquota do XML vem como porcentagem (ex: 3.00 para 3%), então divide por 100
    if aliquota_xml is not None and aliquota_xml > 0:
        return base_calculo * (aliquota_xml / 100)
    # Se não houver alíquota no XML ou ela for zero/inválida, usa uma alíquota de referência
    return base_calculo * ALIQUOTA_ISSQN_REFERENCIA

# NOVO: Função para detectar problemas de sequência de NF
# Linha 194
def detect_sequence_issues(df_input):
    """
    Detecta números de NF duplicados e lacunas na sequência por prestador e competência.
    Retorna um DataFrame com os problemas encontrados.
    df_input deve conter as colunas 'Número da NF', 'Prestador CNPJ', 'Competência', 'Status Cancelamento'.
    """
    # --- NOVO: Verificação de colunas necessárias ---
    required_cols = ['Número da NF', 'Prestador CNPJ', 'Competência', 'Status Cancelamento', 'Prestador Razão Social', 'ID NFSe']
    missing_cols = [col for col in required_cols if col not in df_input.columns]
    
    if missing_cols:
        # Tenta usar log_message_viewer se estiver disponível, senão usa st.warning
        try:
            log_message_viewer(f"Não foi possível realizar a análise de sequência de NF. Colunas ausentes no DataFrame: {', '.join(missing_cols)}", "warning")
        except NameError:
            st.warning(f"Não foi possível realizar a análise de sequência de NF. Colunas ausentes no DataFrame: {', '.join(missing_cols)}")
        
        # Retorna um DataFrame vazio com as colunas esperadas para evitar KeyErrors posteriores
        return pd.DataFrame(columns=[
            'Tipo de Problema', 'Prestador CNPJ', 'Prestador Razão Social', 
            'Competência', 'Número da NF Afetado', 'Detalhes', 'ID NFSe'
        ])
    # --- FIM NOVO ---

    issues = []

    # Certifica que o 'Número da NF' é numérico para ordenação e detecção de gaps
    # Converte para string primeiro para lidar com valores como 'CANCELADA' antes de tentar para numérico
    df_input['Número da NF_int'] = pd.to_numeric(
        df_input['Número da NF'].astype(str).str.replace('CANCELADA', '-1'), errors='coerce'
    ).fillna(-1).astype(int)
    
    # Filtra para números válidos e maiores que zero
    df_filtered = df_input[df_input['Número da NF_int'] > 0].copy()

    # Agrupa por Prestador e Competência
    grouped = df_filtered.groupby(['Prestador CNPJ', 'Competência'])

    for (prestador_cnpj, competencia), group_df in grouped:
        # Ordene as NFs para verificar a sequência
        sorted_nfs = group_df.sort_values(by='Número da NF_int')
        nf_numbers = sorted_nfs['Número da NF_int'].tolist()
        
        if not nf_numbers:
            continue

        # 1. Detectar Duplicatas
        duplicated_numbers = sorted_nfs[sorted_nfs.duplicated(subset=['Número da NF_int'], keep=False)]
        for _, row in duplicated_numbers.iterrows():
            issues.append({
                'Tipo de Problema': 'Número Duplicado',
                'Prestador CNPJ': prestador_cnpj,
                'Prestador Razão Social': row['Prestador Razão Social'],
                'Competência': competencia,
                'Número da NF Afetado': row['Número da NF_int'],
                'Detalhes': f"A NF {row['Número da NF_int']} aparece mais de uma vez.",
                'ID NFSe': row['ID NFSe']
            })

        # 2. Detectar Lacunas (Gaps) na sequência
        # Pegar apenas os números únicos para verificar lacunas
        unique_nf_numbers = sorted(list(set(nf_numbers)))
        
        if len(unique_nf_numbers) < 2:
            continue # Não há sequência para verificar

        for i in range(len(unique_nf_numbers) - 1):
            current_nf = unique_nf_numbers[i]
            next_nf = unique_nf_numbers[i+1]

            if next_nf - current_nf > 1:
                # Há um gap entre current_nf e next_nf
                for missing_num in range(current_nf + 1, next_nf):
                    # Verificar se o número "faltante" foi cancelado no DF original
                    # É importante usar df_input aqui para checar as canceladas também
                    was_cancelled = df_input[(df_input['Prestador CNPJ'] == prestador_cnpj) & 
                                             (df_input['Competência'] == competencia) &
                                             (df_input['Número da NF_int'] == missing_num) & 
                                             (df_input['Status Cancelamento'] == 'Sim')]
                    
                    if not was_cancelled.empty:
                        details = f"A NF {missing_num} está ausente na sequência de NFs ativas, mas foi emitida e CANCELADA."
                        problem_type = 'Número Faltante (Cancelado)'
                        nf_id_details = was_cancelled['ID NFSe'].iloc[0] if not was_cancelled['ID NFSe'].isnull().all() else 'N/A'
                    else:
                        details = f"A NF {missing_num} está ausente na sequência e não foi encontrada como emitida ou cancelada."
                        problem_type = 'Número Faltante (Não Emitido)'
                        nf_id_details = 'N/A'

                    issues.append({
                        'Tipo de Problema': problem_type,
                        'Prestador CNPJ': prestador_cnpj,
                        'Prestador Razão Social': group_df['Prestador Razão Social'].iloc[0], # Pega a razão social do primeiro da lista
                        'Competência': competencia,
                        'Número da NF Afetado': missing_num,
                        'Detalhes': details,
                        'ID NFSe': nf_id_details
                    })
    
    if not issues:
        return pd.DataFrame(columns=[
            'Tipo de Problema', 'Prestador CNPJ', 'Prestador Razão Social', 
            'Competência', 'Número da NF Afetado', 'Detalhes', 'ID NFSe'
        ])
    return pd.DataFrame(issues)


# --- Função para converter e formatar o DataFrame ---
def format_dataframe_for_display(df):
    # Fazer uma cópia para evitar SettingWithCopyWarning
    df_formatted = df.copy()

    # 1. Renomear colunas (colunas existentes serão renomeadas antes de serem usadas nos cálculos)
    # É importante que as chaves de column_display_names (nomes originais) sejam as mesmas do df.
    df_formatted = df_formatted.rename(columns={k: v for k, v in column_display_names.items() if k in df_formatted.columns})

    # 2. Converter tipos de dados e formatar
    # Note que 'Aliquota' não está aqui porque é uma porcentagem e é tratada separadamente no column_config.
    numeric_cols_original_keys_for_conversion = [
        'ValorServicos', 'ValorDeducoes', 'ValorPis', 'ValorCofins', 'ValorInss',
        'ValorIr', 'ValorCsll', 'ValorIss', 'ValorIssRetido', 'OutrasRetencoes',
        'BaseCalculo', 'ValorLiquidoNfse', 'DescontoIncondicionado', 'DescontoCondicionado'
    ]
    
    # Use os nomes já renomeados para o DataFrame
    numeric_cols_display_for_conversion = [column_display_names[key] for key in numeric_cols_original_keys_for_conversion if key in column_display_names]

    for col_disp_name in numeric_cols_display_for_conversion:
        if col_disp_name in df_formatted.columns:
            df_formatted[col_disp_name] = pd.to_numeric(df_formatted[col_disp_name], errors='coerce').fillna(0).astype(float)
    
    # Aliquota é numérica mas tratada como porcentagem na exibição, não precisa de R\$
    if 'Alíquota' in df_formatted.columns:
        df_formatted['Alíquota'] = pd.to_numeric(df_formatted['Alíquota'], errors='coerce').fillna(0).astype(float)


    # Colunas que devem ser datas e cálculo da Competência
    if 'Data Emissão' in df_formatted.columns:
        df_formatted['Data Emissão'] = pd.to_datetime(df_formatted['Data Emissão'], errors='coerce')
        if isinstance(df_formatted['Data Emissão'].dtype, pd.DatetimeTZDtype): # Corrigido: Linha 222 (DeprecationWarning)
            df_formatted['Data Emissão'] = df_formatted['Data Emissão'].dt.tz_localize(None)
        df_formatted['Competência'] = df_formatted['Data Emissão'].dt.strftime('%Y-%m')

    # Mapear códigos para textos legíveis para 'Simples Nacional' e 'ISS Retido (Cód)'
    if 'Simples Nacional' in df_formatted.columns:
        df_formatted['Simples Nacional'] = df_formatted['Simples Nacional'].astype(str).replace({'1': 'Sim', '2': 'Não', '': np.nan}).fillna('Não Informado')
    if 'ISS Retido (Cód)' in df_formatted.columns:
        df_formatted['ISS Retido (Cód)'] = df_formatted['ISS Retido (Cód)'].astype(str).replace({'1': 'Sim', '2': 'Não', '': np.nan}).fillna('Não Informado')

    # Adicionar Prestador Regime
    if 'Simples Nacional' in df_formatted.columns:
        df_formatted['Prestador Regime'] = df_formatted['Simples Nacional'].apply(
            lambda x: 'Simples Nacional' if x == 'Sim' else 'Lucro Presumido' if x == 'Não' else 'Não Informado'
        )

    # Adicionar Tomador Tipo (Pessoa Física/Jurídica)
    if 'Tomador CNPJ/CPF' in df_formatted.columns:
        df_formatted['Tomador Tipo'] = df_formatted['Tomador CNPJ/CPF'].astype(str).str.replace(r'[^0-9]', '', regex=True).apply(
            lambda x: 'Pessoa Física' if len(x) == 11 else 'Pessoa Jurídica' if len(x) == 14 else 'Não Identificado'
        )
    
    # Garantir que 'Status Cancelamento' existe (deve vir do parser, mas como fallback)
    if 'Status Cancelamento' not in df_formatted.columns:
        df_formatted['Status Cancelamento'] = 'Não' # Default para 'Não' se não vier do parser

    # --- 3. Calcular Retenções Esperadas e Status de Conferência ---
    # Inicializa as novas colunas com valores padrão
    df_formatted['IR Esperado'] = 0.0
    df_formatted['CSLL Esperado'] = 0.0
    df_formatted['PIS Esperado'] = 0.0
    df_formatted['COFINS Esperado'] = 0.0
    df_formatted['ISSQN Esperado'] = 0.0

    df_formatted['Status IR'] = 'Não Aplicável'
    df_formatted['Status CSLL'] = 'Não Aplicável'
    df_formatted['Status PIS'] = 'Não Aplicável'
    df_formatted['Status COFINS'] = 'Não Aplicável'
    df_formatted['Status ISS Retido'] = 'Não Aplicável'
    df_formatted['Status Geral Retenções'] = 'Não Aplicável'

    # Itera sobre o DataFrame para aplicar a lógica de conferência
    # Usamos .loc para atribuir valores e evitar SettingWithCopyWarning
    for index, row in df_formatted.iterrows():

        # Cenário A: Nota Cancelada
        if row['Status Cancelamento'] == 'Sim':
            df_formatted.loc[index, ['Status IR', 'Status CSLL', 'Status PIS', 'Status COFINS', 'Status ISS Retido', 'Status Geral Retenções']] = 'Cancelado'
            continue # Pula para a próxima nota

        # Cenário B: Prestador Simples Nacional ou Tomador Pessoa Física
        # Nessas condições, não deveria haver retenção. Se houver, é uma retenção indevida.
        if row['Prestador Regime'] == 'Simples Nacional' or row['Tomador Tipo'] == 'Pessoa Física':
            is_ir_retido = row['IR'] > 0.01
            is_csll_retido = row['CSLL'] > 0.01
            is_pis_retido = row['PIS'] > 0.01
            is_cofins_retido = row['COFINS'] > 0.01
            is_iss_retido = row['Valor ISS Retido'] > 0.01

            df_formatted.loc[index, 'Status IR'] = 'Retenção Indevida' if is_ir_retido else 'OK'
            df_formatted.loc[index, 'Status CSLL'] = 'Retenção Indevida' if is_csll_retido else 'OK'
            df_formatted.loc[index, 'Status PIS'] = 'Retenção Indevida' if is_pis_retido else 'OK'
            df_formatted.loc[index, 'Status COFINS'] = 'Retenção Indevida' if is_cofins_retido else 'OK'
            df_formatted.loc[index, 'Status ISS Retido'] = 'Retenção Indevida' if is_iss_retido else 'OK'
            
            if any([is_ir_retido, is_csll_retido, is_pis_retido, is_cofins_retido, is_iss_retido]):
                df_formatted.loc[index, 'Status Geral Retenções'] = 'INCONSISTÊNCIA (Retenção Indevida)'
            else:
                df_formatted.loc[index, 'Status Geral Retenções'] = 'OK'
            continue

        # Cenário C: Prestador Lucro Presumido e Tomador Pessoa Jurídica (onde retenções são esperadas)
        if row['Prestador Regime'] == 'Lucro Presumido' and row['Tomador Tipo'] == 'Pessoa Jurídica':
            valor_servicos = row['Valor dos Serviços'] # Já convertido para float
            base_calculo = row['Base de Cálculo'] # Já convertido para float
            aliquota_xml = row['Alíquota'] # Já convertido para float

            # IRPJ
            ir_esperado = calcular_irrf_esperado(valor_servicos)
            df_formatted.loc[index, 'IR Esperado'] = ir_esperado
            if np.isclose(row['IR'], ir_esperado, atol=0.01):
                df_formatted.loc[index, 'Status IR'] = 'OK'
            else:
                df_formatted.loc[index, 'Status IR'] = 'Divergência'

            # CSLL, PIS, COFINS (CSRF)
            csrf_esperado_valores = calcular_csrf_esperado(valor_servicos)
            
            df_formatted.loc[index, 'CSLL Esperado'] = csrf_esperado_valores['CSLL']
            if np.isclose(row['CSLL'], csrf_esperado_valores['CSLL'], atol=0.01):
                df_formatted.loc[index, 'Status CSLL'] = 'OK'
            else:
                df_formatted.loc[index, 'Status CSLL'] = 'Divergência'

            df_formatted.loc[index, 'PIS Esperado'] = csrf_esperado_valores['PIS']
            if np.isclose(row['PIS'], csrf_esperado_valores['PIS'], atol=0.01):
                df_formatted.loc[index, 'Status PIS'] = 'OK'
            else:
                df_formatted.loc[index, 'Status PIS'] = 'Divergência'

            df_formatted.loc[index, 'COFINS Esperado'] = csrf_esperado_valores['COFINS']
            if np.isclose(row['COFINS'], csrf_esperado_valores['COFINS'], atol=0.01):
                df_formatted.loc[index, 'Status COFINS'] = 'OK'
            else:
                df_formatted.loc[index, 'Status COFINS'] = 'Divergência'

            
            # ISSQN Retido
            valor_iss_retido_xml = row['Valor ISS Retido']
            iss_retido_xml_code = row['ISS Retido (Cód)'] # 'Sim' ou 'Não' (do mapeamento)
            
            if iss_retido_xml_code == 'Sim': # Se o XML indica que ISS foi retido
                iss_esperado = calcular_issqn_esperado(base_calculo, aliquota_xml)
                df_formatted.loc[index, 'ISSQN Esperado'] = iss_esperado
                if np.isclose(valor_iss_retido_xml, iss_esperado, atol=0.01):
                    df_formatted.loc[index, 'Status ISS Retido'] = 'OK (Conferir Alíquota)'
                else:
                    df_formatted.loc[index, 'Status ISS Retido'] = 'Divergência (ISSQN)'
            elif iss_retido_xml_code == 'Não' and valor_iss_retido_xml > 0.01:
                # O XML diz que não reteve, mas há um valor retido. Isso é uma inconsistência.
                df_formatted.loc[index, 'Status ISS Retido'] = 'Retenção Indevida (ISSQN)'
                df_formatted.loc[index, 'ISSQN Esperado'] = 0.0 # Nao era pra ter retido, entao esperado é 0
            else: # Se o XML não indica retenção ou valor é 0, e não é indevida
                df_formatted.loc[index, 'Status ISS Retido'] = 'Não Retido (OK)'
                df_formatted.loc[index, 'ISSQN Esperado'] = 0.0 # Não retido = 0 esperado

            # Determinar Status Geral de Retenções para este cenário
            statuses = [df_formatted.loc[index, 'Status IR'], df_formatted.loc[index, 'Status CSLL'],
                        df_formatted.loc[index, 'Status PIS'], df_formatted.loc[index, 'Status COFINS'],
                        df_formatted.loc[index, 'Status ISS Retido']]

            if any(s in ['Divergência', 'Retenção Indevida'] for s in statuses):
                df_formatted.loc[index, 'Status Geral Retenções'] = 'INCONSISTÊNCIA'
            elif any(s in ['OK (Conferir Alíquota)', 'Não Retido (OK)'] for s in statuses) and \
                 not any(s in ['Divergência', 'Retenção Indevida'] for s in statuses):
                 df_formatted.loc[index, 'Status Geral Retenções'] = 'OK'
            else: # P. ex., 'Não Aplicável' para todos ou outros casos que podem ser 'OK'
                df_formatted.loc[index, 'Status Geral Retenções'] = 'OK' # Default para OK se não encontrar inconsistências ou atenção específicas
    
    # INÍCIO DA CORREÇÃO: Linha 399 (Formatação para string e uso de TextColumn)
    for col in currency_cols_for_display:
        if col in df_formatted.columns:
            # Formatação para R\$ X.XXX,XX (ponto para milhar, vírgula para decimal)
            # Verifica se o valor é numérico antes de formatar para evitar erro em None/NaN
            if pd.api.types.is_numeric_dtype(df_formatted[col]):
                df_formatted[col] = df_formatted[col].apply(lambda x: f"R$ {x:_.2f}".replace('.', '#').replace('_', '.').replace('#', ',') if pd.notna(x) else None)
            else: # Se já não for numérico (e.g., 'CANCELADA'), mantém como está
                pass
    # FIM DA CORREÇÃO

    # Definição do column_config para o st.dataframe
    # Reconstruímos o dicionário para ter certeza de que as colunas de moeda estão como TextColumn
    config = {
        'Data Emissão': st.column_config.DatetimeColumn(
            "Data Emissão", format="DD/MM/YYYY HH:mm", help="Data e hora de emissão da NFSe"
        ),
        'Competência': st.column_config.TextColumn(
            "Competência", help="Competência (Ano-Mês) da NFSe, derivada da Data de Emissão"
        ),
        'Número da NF': st.column_config.NumberColumn(
            "Número da NF", help="Número sequencial da Nota Fiscal"
        ),
        
        # Colunas de Moeda (agora serão TextColumn pois foram pré-formatadas como string)
        **{col: st.column_config.TextColumn(col) for col in currency_cols_for_display if col in df_formatted.columns},

        # Outras colunas
        'Alíquota': st.column_config.NumberColumn(
            "Alíquota (%)", format="%.2f %%", help="Alíquota do ISS sobre o serviço"
        ),
        'Simples Nacional': st.column_config.TextColumn(
            "Simples Nacional", help="Indicador se o prestador é optante pelo Simples Nacional (Sim/Não)"
        ),
        'ISS Retido (Cód)': st.column_config.TextColumn(
            "ISS Retido?", help="Indicador se o ISS foi retido (Sim/Não)"
        ),
        'Natureza Operacao': st.column_config.TextColumn(
            "Natureza Operação", help="Código da Natureza da Operação"
        ),
        'Tomador Tipo': st.column_config.TextColumn(
            "Tomador Tipo", help="Identifica se o tomador é Pessoa Física ou Jurídica"
        ),
        'Prestador Regime': st.column_config.TextColumn(
            "Prestador Regime", help="Regime tributário do prestador (Simples Nacional ou Lucro Presumido)"
        ),
        'Status Cancelamento': st.column_config.TextColumn(
            "Status Cancelamento", help="Indica se a NFSe foi cancelada (Sim/Não)"
        ),
        
        # Novas colunas de status de conferência
        'Status IR': st.column_config.TextColumn("Status IR", help="Status da conferência de IRRF: OK, Divergência, Retenção Indevida, Cancelado, Não Aplicável"),
        'Status CSLL': st.column_config.TextColumn("Status CSLL", help="Status da conferência de CSLL: OK, Divergência, Retenção Indevida, Cancelado, Não Aplicável"),
        'Status PIS': st.column_config.TextColumn("Status PIS", help="Status da conferência de PIS: OK, Divergência, Retenção Indevida, Cancelado, Não Aplicável"),
        'Status COFINS': st.column_config.TextColumn("Status COFINS", help="Status da conferência de COFINS: OK, Divergência, Retenção Indevida, Cancelado, Não Aplicável"),
        'Status ISS Retido': st.column_config.TextColumn("Status ISS Retido", help="Status da conferência de ISSQN Retido: OK, Divergência, Retenção Indevida, Cancelado, Não Aplicável"),
        'Status Geral Retenções': st.column_config.TextColumn("Status Geral Retenções", help="Status geral da conferência das retenções na NFSe: OK, INCONSISTÊNCIA, ATENÇÃO, Cancelado, Não Aplicável")
    }

    # Adiciona colunas que podem não estar diretamente na lista de moeda, mas que precisam de config
    # Ex: Prestador CNPJ, Tomador CNPJ/CPF
    if 'Prestador CNPJ' in df_formatted.columns:
        config['Prestador CNPJ'] = st.column_config.TextColumn('Prestador CNPJ')
    if 'Tomador CNPJ/CPF' in df_formatted.columns:
        config['Tomador CNPJ/CPF'] = st.column_config.TextColumn('Tomador CNPJ/CPF')


    return df_formatted, config

# --- Seção de Upload de Arquivos XML ---
st.header("1. Upload dos Arquivos XML")
uploaded_files_viewer = st.file_uploader(
    "Arraste e solte seus arquivos XML aqui ou clique para selecionar",
    type=["xml"],
    accept_multiple_files=True,
    key="xml_uploader_viewer"
)

# --- Botão de Processamento Principal ---
st.markdown("---")
# CORREÇÃO: Linha 550 - Substitui use_container_width=True por width='stretch'
if st.button("PROCESSAR XMLs para Visualização", type="primary", width='stretch'):
    st.session_state.log_messages_viewer = []
    st.session_state.df_processed_viewer = None
    st.session_state.selected_columns = default_cols_to_show_initial.copy() # Reseta para a ordem padrão
    st.session_state.column_config = {} # Limpa a config de colunas ao reprocessar
    st.session_state.diagnosis_messages = [] # Limpa as mensagens de diagnóstico
    st.session_state.sequence_issues = pd.DataFrame() # Limpa problemas de sequência ao reprocessar
    
    if not uploaded_files_viewer:
        log_message_viewer("Por favor, faça o upload de pelo menos um arquivo XML.", "error")
    else:
        log_message_viewer("\n--- INICIANDO PROCESSAMENTO NFSe para Visualização ---")
        log_message_viewer(f"Encontrados {len(uploaded_files_viewer)} arquivos XML carregados.")

        try:
            all_extracted_data = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            temp_files_to_clean = []
            
            for i, uploaded_file in enumerate(uploaded_files_viewer):
                progress_percent = (i + 1) / len(uploaded_files_viewer)
                progress_bar.progress(progress_percent)
                status_text.text(f"Processando arquivo: {uploaded_file.name} ({i+1}/{len(uploaded_files_viewer)})")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                temp_files_to_clean.append(tmp_file_path)

                data = extract_nfse_data(tmp_file_path)
                if data:
                    all_extracted_data.append(data)
                else:
                    st.session_state.diagnosis_messages.append(f"⚠️ Atenção: Não foi possível extrair dados completos de **{uploaded_file.name}**.")
                    log_message_viewer(f"Atenção: Não foi possível extrair dados completos de {uploaded_file.name}.", "warning")
            
            progress_bar.empty()
            status_text.empty()
            
            log_message_viewer(f"Total de NFSe com dados extraídos com sucesso: {len(all_extracted_data)}")

            if all_extracted_data:
                df_nfses = pd.DataFrame(all_extracted_data)
                
                # A formatação é feita aqui, e o st.session_state.column_config é preenchido
                st.session_state.df_processed_viewer, st.session_state.column_config = format_dataframe_for_display(df_nfses)
                
                # NOVO: Detecta problemas de sequência
                # Corrigido: Linha 609 - Passa o DataFrame JÁ PROCESSADO e RENOMEADO para a função detect_sequence_issues
                st.session_state.sequence_issues = detect_sequence_issues(st.session_state.df_processed_viewer.copy())
                
                log_message_viewer(f"\nProcessamento dos XMLs concluído para visualização!", "success")
                st.success(f"Processamento dos XMLs concluído! Visualize os dados abaixo.")

            else:
                log_message_viewer("Nenhum dado de NFSe válido foi extraído dos arquivos XML carregados.", "warning")
                st.warning("Nenhum dado de NFSe válido foi extraído para visualização.")

        except Exception as e:
            log_message_viewer(f"ERRO CRÍTICO DURANTE O PROCESSAMENTO: {e}", "error")
            st.error(f"Ocorreu um erro durante o processamento: {e}")
        finally:
            for tfp in temp_files_to_clean:
                try:
                    os.remove(tfp)
                except OSError as e:
                    log_message_viewer(f"Erro ao remover arquivo temporário {tfp}: {e}", "error")


# --- Exibição de Resultados e Logs ---
st.header("2. Conferência de Notas Fiscais e Diagnóstico")

if st.session_state.df_processed_viewer is not None and not st.session_state.df_processed_viewer.empty:
    df_full = st.session_state.df_processed_viewer.copy()  # Trabalhar com uma cópia

    if 'Competência' in df_full.columns:
        # Padronizar a coluna Competência
        df_full['Competência'] = pd.to_datetime(
            df_full['Competência'], format='%Y-%m', errors='coerce'
        ).dt.strftime('%Y-%m')  # Formatar no padrão YYYY-MM

        # Remove valores NaN/NaT resultantes da conversão inválida
        df_full = df_full.dropna(subset=['Competência'])

        # Ordenar as competências únicas de forma decrescente
        available_competencias = sorted(df_full['Competência'].unique(), reverse=True)
    else:
        st.warning("A coluna 'Competência' não foi encontrada no DataFrame.")
        available_competencias = []

    # --- Seletor de Competência ---
if 'Competência' in df_full.columns:
    # Garantir que a coluna Competência esteja no formato correto (YYYY-MM)
    df_full['Competência'] = pd.to_datetime(
        df_full['Competência'], format='%Y-%m', errors='coerce'
    ).dt.strftime('%Y-%m')  # Formata para ano-mês

    # Remove valores inválidos (NaT ou células sem dados)
    df_full = df_full.dropna(subset=['Competência'])

    # Ordena as competências de maneira decrescente
    available_competencias = sorted(df_full['Competência'].unique(), reverse=True)
else:
    st.warning("A coluna 'Competência' não foi encontrada no DataFrame.")
    available_competencias = df_full['Competência'].unique().tolist() if 'Competência' in df_full.columns else []
    # Garantir que a coluna Competência esteja no formato correto (YYYY-MM)
    df_full['Competência'] = pd.to_datetime(
        df_full['Competência'], format='%Y-%m', errors='coerce'
    ).dt.strftime('%Y-%m')  # Formata para ano-mês

    # Remove valores inválidos (NaT ou células sem dados)
    df_full = df_full.dropna(subset=['Competência'])

    # Ordena as competências de maneira decrescente
    if 'Competência' in df_full.columns:
        available_competencias = df_full['Competência'].unique().tolist()
        available_competencias = sorted(available_competencias)
    else:
        available_competencias = []
    st.warning("A coluna 'Competência' não foi encontrada no DataFrame.")
    available_competencias = []
    if not available_competencias:
        st.warning("Não foi possível extrair competências das NFSe carregadas.")
        selected_competence = None
        df_competence = pd.DataFrame() # DataFrame vazio se não houver competências
    else:
        selected_competence = st.selectbox(
            "Selecione a competência para conferência:",
            options=available_competencias,
            help="Selecione o mês e ano para o qual você deseja conferir as notas fiscais."
        )
        # Filtra o DataFrame pela competência selecionada
        df_competence = df_full[df_full['Competência'] == selected_competence].copy()

    if selected_competence and not df_competence.empty:
        # NOVO: Filtra as notas ativas (não canceladas) para cálculos e diagnósticos
        df_active_notes = df_competence[df_competence['Status Cancelamento'] == 'Não'].copy()

        # --- Informações do Prestador e Painel de Impostos (Baseado na competência e notas ATIVAS) ---
        st.subheader(f"Visão Geral da Competência: {selected_competence}")
        
        unique_prestadores = df_active_notes['Prestador Razão Social'].unique() # Usa df_active_notes
        
        lucro_presumido_tipo_selection = "Normal" # Valor padrão para garantir que sempre haja um tipo selecionado

        if len(unique_prestadores) == 1:
            if not df_active_notes.empty: # Garante que há pelo menos uma nota ativa para pegar a info
                prestador_info = df_active_notes.iloc[0]
                prestador_nome = prestador_info['Prestador Razão Social']
                prestador_cnpj = prestador_info['Prestador CNPJ']
                prestador_regime = prestador_info['Prestador Regime']

                st.write(f"**Nome do Prestador:** {prestador_nome}")
                st.write(f"**CNPJ do Prestador:** {prestador_cnpj}")
                st.write(f"**Regime Tributário Aparente:** {prestador_regime}")

                if prestador_regime == "Lucro Presumido":
                    st.warning("Atenção: Os cálculos de impostos abaixo são feitos com base no regime de Lucro Presumido.")
                    lucro_presumido_tipo_selection = st.selectbox(
                        "Selecione o tipo de Lucro Presumido para os cálculos:",
                        ["Normal", "Equiparação Hospitalar"],
                        index=0 # Padrão "Normal"
                    )
                    ## if lucro_presumido_tipo_selection == "Equiparação Hospitalar":
                    #    st.info("O cálculo para 'Equiparação Hospitalar' ainda não foi implementado. Exibindo cálculos para 'Normal'.")
                elif prestador_regime == "Simples Nacional":
                    st.info("O prestador é do Simples Nacional. Os cálculos de impostos detalhados para Lucro Presumido não se aplicam diretamente aqui.")
                else: # 'Não Informado' ou outro
                     st.info("Regime tributário do prestador não identificado para cálculo de impostos.")

        elif len(unique_prestadores) > 1:
            st.warning("Foram encontrados múltiplos prestadores (notas ativas) para esta competência. O resumo abaixo agregará os dados de todos eles. As informações do prestador principal podem não representar todo o conjunto. Os cálculos de impostos são baseados em Lucro Presumido (Normal).")
            if not df_active_notes.empty: # Garante que há pelo menos uma nota ativa
                first_prestador_info = df_active_notes.iloc[0]
                st.write(f"**Primeiro Prestador Encontrado:** {first_prestador_info['Prestador Razão Social']} (CNPJ: {first_prestador_info['Prestador CNPJ']})")
            
            lucro_presumido_tipo_selection = st.selectbox(
                "Selecione o tipo de Lucro Presumido para os cálculos (aplicado a todos os dados):",
                ["Normal", "Equiparação Hospitalar"],
                index=0 # Padrão "Normal"
            )
            #if lucro_presumido_tipo_selection == "Equiparação Hospitalar (Ainda não implementado)":
            #    st.info("O cálculo para 'Equiparação Hospitalar' ainda não foi implementado. Exibindo cálculos para 'Normal'.")

        else: # Nenhuma NFSe ATIVA para a competência selecionada
            st.info("Não há dados de NFSe ATIVAS para a competência selecionada ou não foi possível identificar as informações do prestador.")
            
        st.markdown("---") # Separador visual

        # --- Painel de Dados: Faturamento e Impostos (Baseado em notas ATIVAS) ---
        st.subheader("Painel de Faturamento e Impostos (Notas Ativas)")

        # Verifica se há notas ativas antes de calcular
        if df_active_notes.empty:
            st.info("Não há notas ativas para calcular o painel de faturamento e impostos.")
            total_faturamento = 0.0
            total_ir_retido = 0.0
            total_csll_retido = 0.0
            total_pis_retido = 0.0
            total_cofins_retido = 0.0
            total_iss_retido = 0.0
            base_calculo_issqn = 0.0
            total_liquido_recebido = 0.0
        else:
            # Desformata temporariamente para fazer os cálculos, pois os valores estão em string "R\$ X.XXX,XX"
            # df_active_notes é uma cópia, então não afetará o df_full original que já está formatado para display.
            # Convertemos para float para somar.
            temp_df = df_active_notes.copy()
            for col in currency_cols_for_display:
                if col in temp_df.columns:
                    # Remove "R\$", pontos de milhar, e troca vírgula por ponto decimal para converter em float
                    temp_df[col] = temp_df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce').fillna(0).astype(float)


            # Faturamento
            total_faturamento = temp_df['Valor dos Serviços'].sum()

            # Impostos Retidos
            total_ir_retido = temp_df['IR'].sum()
            total_csll_retido = temp_df['CSLL'].sum()
            total_pis_retido = temp_df['PIS'].sum()
            total_cofins_retido = temp_df['COFINS'].sum()
            total_iss_retido = temp_df['Valor ISS Retido'].sum()
            
            # Base de Cálculo para ISSQN
            base_calculo_issqn = temp_df['Base de Cálculo'].sum()
            total_liquido_recebido = temp_df['Valor Líquido NFSe'].sum()


        # --- Cálculos para Lucro Presumido (Normal) ---
        irpj_a_pagar = 0.0
        csll_a_pagar = 0.0
        pis_a_pagar = 0.0
        cofins_a_pagar = 0.0
        issqn_a_pagar = 0.0

        if lucro_presumido_tipo_selection == "Normal": # Apenas se o tipo selecionado for "Normal"
            # IRPJ: Faturamento * 4.8% - IR Retido
            irpj_a_pagar = (total_faturamento * 0.048) - total_ir_retido
            # CSLL: Faturamento * 2.88% - CSLL Retida
            csll_a_pagar = (total_faturamento * 0.0288) - total_csll_retido
            # PIS: Faturamento * 0.0065 - PIS Retido
            pis_a_pagar = (total_faturamento * 0.0065) - total_pis_retido
            # COFINS: Faturamento * 0.03 - COFINS Retida
            cofins_a_pagar = (total_faturamento * 0.03) - total_cofins_retido
            # ISSQN: Base de Cálculo * Alíquota de Referência (se não retido) - ISS Retido
            issqn_a_pagar = (base_calculo_issqn * ALIQUOTA_ISSQN_REFERENCIA) - total_iss_retido
       
        # NOVO BLOCO: Cálculos para Lucro Presumido - Equiparação Hospitalar
        elif lucro_presumido_tipo_selection == "Equiparação Hospitalar":
            # IRPJ: Faturamento * 1.2% - IR Retido
            irpj_a_pagar = (total_faturamento * ALIQUOTA_IRPJ_EQ_HOSP) - total_ir_retido
            # CSLL: Faturamento * 1.08% - CSLL Retida
            csll_a_pagar = (total_faturamento * ALIQUOTA_CSLL_EQ_HOSP) - total_csll_retido
            # PIS: Faturamento * 0.65% - PIS Retido
            pis_a_pagar = (total_faturamento * ALIQUOTA_PIS_EQ_HOSP) - total_pis_retido
            # COFINS: Faturamento * 3.00% - COFINS Retida
            cofins_a_pagar = (total_faturamento * ALIQUOTA_COFINS_EQ_HOSP) - total_cofins_retido
            # ISSQN: Faturamento * 2.01% - ISS Retido (agora com base no faturamento)
            issqn_a_pagar = (total_faturamento * ALIQUOTA_ISSQN_EQ_HOSP) - total_iss_retido
        # Garante que os valores a pagar não são negativos (imposto já retido a maior)
        irpj_a_pagar = max(0, irpj_a_pagar)
        csll_a_pagar = max(0, csll_a_pagar)
        pis_a_pagar = max(0, pis_a_pagar)
        cofins_a_pagar = max(0, cofins_a_pagar)
        issqn_a_pagar = max(0, issqn_a_pagar)

        total_impostos_a_pagar = irpj_a_pagar + csll_a_pagar + pis_a_pagar + cofins_a_pagar + issqn_a_pagar

        # Layout com colunas para o painel
        st.markdown("### Valores Gerais")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de NFSe Ativas Processadas", len(df_active_notes))
        with col2:
            st.metric("Total Faturamento Bruto", f"R$ {total_faturamento:,.2f}")
        with col3:
            st.metric("Valor Líquido Recebido (NFSe)", f"R$ {total_liquido_recebido:,.2f}")

        st.markdown("### Impostos Retidos")
        col_ir_ret, col_csll_ret, col_pis_ret, col_cofins_ret, col_iss_ret = st.columns(5)
        with col_ir_ret:
            st.metric("IR Retido", f"R$ {total_ir_retido:,.2f}")
        with col_csll_ret:
            st.metric("CSLL Retida", f"R$ {total_csll_retido:,.2f}")
        with col_pis_ret:
            st.metric("PIS Retido", f"R$ {total_pis_retido:,.2f}")
        with col_cofins_ret:
            st.metric("COFINS Retida", f"R$ {total_cofins_retido:,.2f}")
        with col_iss_ret:
            st.metric("ISS Retido", f"R$ {total_iss_retido:,.2f}")

        st.markdown("### Impostos a Pagar (Estimativa Lucro Presumido - Normal)")
        col_ir_pagar, col_csll_pagar, col_pis_pagar, col_cofins_pagar, col_iss_pagar, col_total_pagar = st.columns(6)
        with col_ir_pagar:
            st.metric("IRPJ a Pagar", f"R$ {irpj_a_pagar:,.2f}")
        with col_csll_pagar:
            st.metric("CSLL a Pagar", f"R$ {csll_a_pagar:,.2f}")
        with col_pis_pagar:
            st.metric("PIS a Pagar", f"R$ {pis_a_pagar:,.2f}")
        with col_cofins_pagar:
            st.metric("COFINS a Pagar", f"R$ {cofins_a_pagar:,.2f}")
        with col_iss_pagar:
            st.metric("ISSQN a Pagar", f"R$ {issqn_a_pagar:,.2f}")
        with col_total_pagar:
            st.metric("Total Impostos a Pagar", f"R$ {total_impostos_a_pagar:,.2f}")

        st.markdown("---") # Separador visual

        # --- NOVA SEÇÃO: Dashboard de Retenções e Validações ---
        st.header("3. Dashboard de Retenções e Validações")

        if df_active_notes.empty:
            st.info("Não há notas ativas para exibir no dashboard de retenções.")
        else:
            total_nfs = len(df_active_notes)
            nfs_canceladas = len(df_competence[df_competence['Status Cancelamento'] == 'Sim'])
            
            inconsistencias_gerais = df_active_notes[df_active_notes['Status Geral Retenções'].str.contains('INCONSISTÊNCIA', na=False)]
            total_inconsistencias_gerais = len(inconsistencias_gerais)

            atencao_geral = df_active_notes[df_active_notes['Status Geral Retenções'].str.contains('ATENÇÃO', na=False)]
            total_atencao_geral = len(atencao_geral)
            
            col_dash1, col_dash2, col_dash3, col_dash4 = st.columns(4)
            with col_dash1:
                st.metric("Total de NFSe na Competência", len(df_competence))
            with col_dash2:
                st.metric("NFSe Ativas", total_nfs)
            with col_dash3:
                st.metric("NFSe Canceladas", nfs_canceladas)
            with col_dash4:
                st.metric("NFSe com Inconsistências (Geral)", total_inconsistencias_gerais + total_atencao_geral)
            
            st.markdown("### Análise Detalhada das Inconsistências por Imposto")

            # Contar o número de cada tipo de inconsistência por imposto
            inconsistency_counts = {}
            for tax_status_col in ['Status IR', 'Status CSLL', 'Status PIS', 'Status COFINS', 'Status ISS Retido']:
                # Filtra apenas status que não são 'OK', 'Cancelado' ou 'Não Aplicável'
                filtered_statuses = df_active_notes[
                    ~df_active_notes[tax_status_col].isin(['OK', 'Cancelado', 'Não Aplicável', 'OK (Conferir Alíquota)', 'Não Retido (OK)'])
                ][tax_status_col]
                
                # Agrupa os status diferentes de OK/NA
                if not filtered_statuses.empty:
                    counts = filtered_statuses.value_counts().to_dict()
                    for status, count in counts.items():
                        # Concatena o nome do imposto com o status para o gráfico
                        key = f"{tax_status_col.replace('Status ', '')} - {status}"
                        inconsistency_counts[key] = inconsistency_counts.get(key, 0) + count
            
            if inconsistency_counts:
                # Ordena para melhor visualização
                sorted_inconsistencies = sorted(inconsistency_counts.items(), key=lambda item: item[1], reverse=True)
                
                chart_data = {
                    "type": "bar",
                    "title": {
                        "text": f"Distribuição das Inconsistências de Retenção ({selected_competence})"
                    },
                    "series": [
                        {
                            "name": "Número de Notas",
                            "data": [item[1] for item in sorted_inconsistencies],
                            "type": "bar",
                            "marker": {
                                "color": ["#FF0000" if "INDEV" in item[0].upper() or "DIVERG" in item[0].upper() else "#FFA500" for item in sorted_inconsistencies]
                            }
                        }
                    ],
                    "categories": [item[0] for item in sorted_inconsistencies]
                }
                
                # Exibe o gráfico (o front-end irá renderizá-lo a partir do JSON)
                st.json(chart_data)
                
                # Expansor para ver as notas com inconsistências
                with st.expander("Ver Notas com Inconsistências ou Alertas"):
                    if not inconsistencias_gerais.empty or not atencao_geral.empty:
                        # Combina as notas com inconsistência e atenção
                        problematic_notes_df = pd.concat([inconsistencias_gerais, atencao_geral]).drop_duplicates(subset=['Número da NF'])
                        
                        st.write("Abaixo estão as NFSe que requerem atenção devido a inconsistências ou alertas de retenção:")
                        
                        # NOVO: Loop para "printar" cada inconsistência
                        for idx, row in problematic_notes_df.iterrows():
                            st.markdown(f"---")
                            st.markdown(f"### NF nº {row['Número da NF']} - {row['Tomador Razão Social']}")
                            st.markdown(f"**Valor dos Serviços:** {row['Valor dos Serviços']}")
                            st.markdown(f"**Status Geral da Retenção:** **`{row['Status Geral Retenções']}`**")
                            
                            st.markdown("  **Detalhes Específicos:**")
                            problem_found_in_detail = False
                            tax_status_cols = ['Status IR', 'Status CSLL', 'Status PIS', 'Status COFINS', 'Status ISS Retido']
                            for tax_col in tax_status_cols:
                                status = row[tax_col]
                                # Considera como problema ou alerta qualquer status que não seja "OK", "Não Aplicável", "Cancelado",
                                # "OK (Conferir Alíquota)" ou "Não Retido (OK)".
                                if status not in ['OK', 'Não Aplicável', 'Cancelado', 'OK (Conferir Alíquota)', 'Não Retido (OK)']:
                                    tax_name = tax_col.replace('Status ', '').replace(' Retido', ' Ret.') # Para display mais conciso
                                    st.markdown(f"  - **{tax_name}:** `{status}`")
                                    problem_found_in_detail = True
                            
                            if not problem_found_in_detail:
                                st.markdown("  - *Nenhum problema específico detalhado além do status geral (pode ser uma inconsistência sutil ou 'ATENÇÃO').*")
                        
                        st.markdown(f"---") # Separador final após o loop
                        
                        st.write("---") # Separador antes da tabela resumida
                        st.write("### Tabela Resumida de Inconsistências (Visão Geral)")
                        st.dataframe(
                            problematic_notes_df[[
                                'Número da NF', 'Tomador Razão Social', 'Valor dos Serviços', 'Status Geral Retenções',
                                'Status IR', 'Status CSLL', 'Status PIS', 'Status COFINS', 'Status ISS Retido'
                            ]],
                            width='stretch',
                            hide_index=True
                        )
                        st.info("Para detalhes completos de todas as colunas, utilize o seletor de colunas na seção 'Detalhes das NFSe'.")
                    else:
                        st.success("🎉 Nenhuma NFSe com inconsistências ou alertas para mostrar nesta competência!")
            else:
                st.success("�� Nenhuma inconsistência de retenção encontrada para as notas ativas nesta competência!")


        st.markdown("---") # Separador visual

        # NOVO: Seção de Análise de Sequência de Notas Fiscais
        # Linha 827
        st.header("4. Análise de Sequência de Notas Fiscais") # Reordenado para 4, antes era 5

        if not st.session_state.sequence_issues.empty:
            # Filtra os problemas de sequência para a competência selecionada
            current_competence_issues = st.session_state.sequence_issues[
                st.session_state.sequence_issues['Competência'] == selected_competence
            ]

            if not current_competence_issues.empty:
                st.subheader(f"Problemas de Sequência Encontrados para {selected_competence}")
                
                total_issues = len(current_competence_issues)
                num_duplicates = len(current_competence_issues[current_competence_issues['Tipo de Problema'] == 'Número Duplicado'])
                num_missing_cancelled = len(current_competence_issues[current_competence_issues['Tipo de Problema'] == 'Número Faltante (Cancelado)'])
                num_missing_never_issued = len(current_competence_issues[current_competence_issues['Tipo de Problema'] == 'Número Faltante (Não Emitido)'])

                col_seq1, col_seq2, col_seq3, col_seq4 = st.columns(4)
                with col_seq1:
                    st.metric("Total de Problemas", total_issues)
                with col_seq2:
                    st.metric("Nº Duplicados", num_duplicates)
                with col_seq3:
                    st.metric("Nº Faltantes (Cancelado)", num_missing_cancelled)
                with col_seq4:
                    st.metric("Nº Faltantes (Não Emitido)", num_missing_never_issued)

                st.markdown("### Detalhes dos Problemas de Sequência")
                # CORREÇÃO: Linha 891 - Substitui use_container_width=True por width='stretch'
                st.dataframe(
                    current_competence_issues,
                    width='stretch',
                    hide_index=True
                )

                # Gráfico de problemas por tipo
                issue_counts = current_competence_issues['Tipo de Problema'].value_counts().reset_index()
                issue_counts.columns = ['Tipo de Problema', 'Contagem']
                
                chart_data_sequence = {
                    "type": "bar",
                    "title": {
                        "text": f"Distribuição dos Problemas de Sequência de NF ({selected_competence})"
                    },
                    "series": [
                        {
                            "name": "Contagem",
                            "data": issue_counts['Contagem'].tolist(),
                            "type": "bar",
                            "marker": {
                                "color": [
                                    "#FF4B4B" if "Duplicado" in t else "#FFA500" if "Cancelado" in t else "#FF0000" 
                                    for t in issue_counts['Tipo de Problema']
                                ]
                            }
                        }
                    ],
                    "categories": issue_counts['Tipo de Problema'].tolist()
                }
                st.json(chart_data_sequence)

            else:
                st.success(f"🎉 Nenhuma inconsistência de sequência de NF encontrada para {selected_competence}!")
        else:
            st.info("Carregue e processe os XMLs para analisar a sequência de notas fiscais.")
            
        st.markdown("---") # Separador visual


        # --- Tabela de Dados (filtrada pela competência, incluindo CANCELADAS) ---
        st.subheader("5. Detalhes das NFSe (Competência Selecionada)") # Reordenado para 5, antes era 4
        st.markdown("Aqui você pode ver todos os detalhes das notas fiscais e selecionar as colunas que deseja exibir.")
        # Selector de colunas
        with st.expander("Gerenciar Colunas", expanded=False):
            # Obtém todas as colunas que estão no DataFrame atual
            all_available_display_cols = list(df_full.columns)
            
            # Garante que as colunas padrão que queremos exibir existam no DataFrame
            initial_selection = [col for col in default_cols_to_show_initial if col in all_available_display_cols]
            # Adiciona as colunas de status e esperado à lista de opções, mas não à seleção padrão
            additional_cols_for_selection = [
                'IR Esperado', 'CSLL Esperado', 'PIS Esperado', 'COFINS Esperado', 'ISSQN Esperado',
                'Status IR', 'Status CSLL', 'Status PIS', 'Status COFINS', 'Status ISS Retido', 'Status Geral Retenções'
            ]
            # Adiciona as colunas adicionais na lista de opções para o multiselect
            for col in additional_cols_for_selection:
                if col in all_available_display_cols and col not in initial_selection:
                    initial_selection.append(col) # Adiciona se não estiver já na seleção inicial

            st.session_state.selected_columns = st.multiselect(
                "Selecione as colunas para exibir:",
                options=all_available_display_cols,
                default=[col for col in initial_selection if col in all_available_display_cols],
                key="column_selector"
            )
            
        if st.session_state.selected_columns:
            # df_to_display continua usando df_competence para mostrar todas as NFs, inclusive canceladas.
            df_to_display = df_competence[st.session_state.selected_columns]
            # CORREÇÃO: Linha 960 - Substitui use_container_width=True por width='stretch'
            st.dataframe(
                df_to_display,
                column_config=st.session_state.column_config,
                width='stretch',
                hide_index=True
            )

            # --- Botões de Download ---
            st.subheader("Opções de Download:")
            col_csv, col_excel = st.columns(2)

            # Download CSV
            with col_csv:
                # INÍCIO DA CORREÇÃO: Desformatação para exportação
                df_desformatted_for_export = df_to_display.copy()
                for col in currency_cols_for_display:
                    if col in df_desformatted_for_export.columns:
                        # Remove "R\$", pontos de milhar, e troca vírgula por ponto decimal
                        df_desformatted_for_export[col] = df_desformatted_for_export[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        df_desformatted_for_export[col] = pd.to_numeric(df_desformatted_for_export[col], errors='coerce')
                
                csv_data = df_desformatted_for_export.to_csv(index=False).encode('utf-8')
                # FIM DA CORREÇÃO
                # CORREÇÃO: Linha 985 - Substitui use_container_width=True por width='stretch'
                st.download_button(
                    label="Baixar como CSV",
                    data=csv_data,
                    file_name=f"nfse_data_{selected_competence}.csv",
                    mime="text/csv",
                    width='stretch'
                )
            
            # Download Excel
            with col_excel:
                # INÍCIO DA CORREÇÃO: Desformatação para exportação
                df_desformatted_for_export = df_to_display.copy()
                for col in currency_cols_for_display:
                    if col in df_desformatted_for_export.columns:
                        # Remove "R\$", pontos de milhar, e troca vírgula por ponto decimal
                        df_desformatted_for_export[col] = df_desformatted_for_export[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                        df_desformatted_for_export[col] = pd.to_numeric(df_desformatted_for_export[col], errors='coerce')

                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df_desformatted_for_export.to_excel(writer, index=False, sheet_name=f'NFSe Data {selected_competence}')
                excel_buffer.seek(0) # Volta para o início do buffer
                # FIM DA CORREÇÃO
                # CORREÇÃO: Linha 1004 - Substitui use_container_width=True por width='stretch'
                st.download_button(
                    label="Baixar como Excel",
                    data=excel_buffer,
                    file_name=f"nfse_data_{selected_competence}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )
    if available_competencias:
    selected_competence = st.selectbox(
        "Selecione a competência para conferência:",
        options=available_competencias,
        help="Selecione o mês e ano para o qual você deseja conferir as notas fiscais."
    )

    # Filtra o DataFrame pela competência selecionada
    df_competence = df_full[df_full['Competência'] == selected_competence].copy()

    if selected_competence and not df_competence.empty:
        st.info(f"Exibindo dados para a competência: {selected_competence}")
    else:
        st.info(f"Nenhuma NFSe encontrada para a competência **{selected_competence}**.")
else:
    st.warning("Não há competências disponíveis para conferência.")
    else:
        st.info("Selecione uma competência acima para visualizar os dados.")
st.subheader("Log de Atividades:")
log_container_viewer = st.container(height=300, border=True)
for message, level in st.session_state.log_messages_viewer:
    if level == "error":
        log_container_viewer.error(message)
    elif level == "warning":
        log_container_viewer.warning(message)
    elif level == "success":
        log_container_viewer.success(message)
    else:
        log_container_viewer.info(message)

st.markdown("---")
st.warning("""
    **Disclaimer Importante:** As informações e os cálculos de impostos apresentados nesta ferramenta são **estimativas** baseadas nos dados extraídos das NFSe e nas alíquotas padrão fornecidas para o regime de Lucro Presumido (Normal). 
    As alíquotas e limites para cálculo das retenções esperadas são valores de referência e **podem necessitar de ajustes** de acordo com a legislação específica do seu município, tipo de serviço, regime tributário exato do prestador e tomador, e outras particularidades fiscais.

    Esta ferramenta **não substitui** a consulta e a análise de um contador ou profissional fiscal qualificado.      
    As regras tributárias podem variar e são complexas. Utilize estes dados apenas como referência e para facilitar a conferência inicial.
""")




from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ====== CONFIGURAÇÕES INICIAIS ======
# Criar o arquivo do SQLite (salvo como "database.db")
engine = create_engine("sqlite:///database.db")
Base = declarative_base()

# ====== CRIAR A TABELA "NFS-e" ======
class NFSe(Base):
    __tablename__ = "nfses"
    id = Column(Integer, primary_key=True)  # ID único para cada registro
    cliente = Column(String(255), nullable=False)  # Nome do cliente
    data_envio = Column(String(50), nullable=False)  # Data de upload
    arquivo_xml = Column(Text, nullable=False)  # Conteúdo do XML salvo como texto

# Criar as tabelas no banco de dados
Base.metadata.create_all(engine)

# Configurar conexão com o banco e criar uma sessão para adicionar/registros
Session = sessionmaker(bind=engine)
session = Session()




















