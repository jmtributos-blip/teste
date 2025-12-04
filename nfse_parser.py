# nfse_parser.py - Arquivo para extração de dados de diferentes layouts de XML NFSe

import xml.etree.ElementTree as ET
import re
import numpy as np
import os # Importado para usar os.path.basename em mensagens de log

# A default dictionary to ensure all expected keys are always present
# This helps maintain a consistent DataFrame structure even if some fields are missing in an XML
_DEFAULT_NFSE_DATA = {
    'Nfse.Id': None,
    'Numero': None,
    'CodigoVerificacao': None,
    'DataEmissao': None,
    'NaturezaOperacao': None,
    'RegimeEspecialTributacao': None,
    'OptanteSimplesNacional': None,
    'IncentivadorCultural': None,
    'DescricaoServico': None,
    'ItemListaServico': None,
    'CodigoTributacaoMunicipio': None,
    'CodigoMunicipioServico': None,
    'ValorServicos': None,
    'ValorDeducoes': None,
    'ValorPis': None,
    'ValorCofins': None,
    'ValorInss': None,
    'ValorIr': None,
    'ValorCsll': None,
    'IssRetido': None, # Código: 1=Sim, 2=Não
    'ValorIss': None,
    'ValorIssRetido': None,
    'OutrasRetencoes': None,
    'BaseCalculo': None,
    'Aliquota': None,
    'ValorLiquidoNfse': None,
    'DescontoIncondicionado': None,
    'DescontoCondicionado': None,
    'Prestador.CpfCnpj': None,
    'Prestador.InscricaoMunicipal': None,
    'Prestador.RazaoSocial': None,
    'Prestador.Endereco.Logradouro': None,
    'Prestador.Endereco.Numero': None,
    'Prestador.Endereco.Complemento': None,
    'Prestador.Endereco.Bairro': None,
    'Prestador.Endereco.CodigoMunicipio': None,
    'Prestador.Endereco.Uf': None,
    'Prestador.Endereco.Cep': None,
    'Prestador.Contato.Telefone': None,
    'Prestador.Contato.Email': None,
    'TomadorServico.CpfCnpj': None,
    'TomadorServico.RazaoSocial': None,
    'TomadorServico.Endereco.Logradouro': None,
    'TomadorServico.Endereco.Numero': None,
    'TomadorServico.Endereco.Bairro': None,
    'TomadorServico.Endereco.CodigoMunicipio': None,
    'TomadorServico.Endereco.Uf': None,
    'TomadorServico.Endereco.Cep': None,
    'TomadorServico.Contato.Telefone': None,
    'OrgaoGerador.CodigoMunicipio': None,
    'OrgaoGerador.Uf': None,
    'IsCancelled': 'Não' # NOVO CAMPO: Assume não cancelada por padrão
}

# --- Funções Auxiliares para Extração de XML ---
def _get_text_or_none(element, xpath, namespaces=None):
    """Extrai o texto de um elemento XML usando XPath, ou None se não encontrado."""
    if element is None:
        return None
    found_elem = element.find(xpath, namespaces=namespaces)
    return found_elem.text if found_elem is not None else None

def _get_attr_or_none(element, xpath, attr_name, namespaces=None):
    """Extrai o valor de um atributo de um elemento XML usando XPath, ou None se não encontrado."""
    if element is None:
        return None
    found_elem = element.find(xpath, namespaces=namespaces)
    return found_elem.get(attr_name) if found_elem is not None else None

def _clean_cnpj_cpf(cnpj_cpf_str):
    """Remove caracteres não numéricos de um CNPJ/CPF."""
    if cnpj_cpf_str:
        return re.sub(r'[^0-9]', '', str(cnpj_cpf_str))
    return None

# --- Parser Específico para o Novo Layout GISS ---
def _parse_giss_nfse(root):
    """Extrai dados de NFSe no layout GISS (com namespace ns2)."""
    data = _DEFAULT_NFSE_DATA.copy() # Inicia com todas as chaves padrão
    
    # Define os namespaces para o XML GISS
    ns_giss = {'ns2': 'http://www.giss.com.br/tipos-v2_04.xsd', 'ns3': 'http://www.w3.org/2000/09/xmldsig#'}
    
    # Busca pelos elementos principais
    inf_nfse = root.find('.//ns2:InfNfse', ns_giss)
    declaracao_prestacao_servico = root.find('.//ns2:DeclaracaoPrestacaoServico/ns2:InfDeclaracaoPrestacaoServico', ns_giss)
    servico_values = root.find('.//ns2:DeclaracaoPrestacaoServico/ns2:InfDeclaracaoPrestacaoServico/ns2:Servico/ns2:Valores', ns_giss)

    print(f"DEBUG GISS: inf_nfse found: {inf_nfse is not None}")
    print(f"DEBUG GISS: declaracao_prestacao_servico found: {declaracao_prestacao_servico is not None}")
    print(f"DEBUG GISS: servico_values found: {servico_values is not None}")

    # NFSe Geral
    data['Nfse.Id'] = _get_attr_or_none(inf_nfse, '.', 'Id', ns_giss)
    data['Numero'] = _get_text_or_none(inf_nfse, 'ns2:Numero', ns_giss)
    data['CodigoVerificacao'] = _get_text_or_none(inf_nfse, 'ns2:CodigoVerificacao', ns_giss)
    data['DataEmissao'] = _get_text_or_none(inf_nfse, 'ns2:DataEmissao', ns_giss)
    data['OptanteSimplesNacional'] = _get_text_or_none(declaracao_prestacao_servico, 'ns2:OptanteSimplesNacional', ns_giss)
    data['IncentivadorCultural'] = _get_text_or_none(declaracao_prestacao_servico, 'ns2:IncentivoFiscal', ns_giss)

    # Serviço
    data['DescricaoServico'] = _get_text_or_none(declaracao_prestacao_servico, 'ns2:Servico/ns2:Discriminacao', ns_giss)
    data['ItemListaServico'] = _get_text_or_none(declaracao_prestacao_servico, 'ns2:Servico/ns2:ItemListaServico', ns_giss)
    data['CodigoTributacaoMunicipio'] = _get_text_or_none(declaracao_prestacao_servico, 'ns2:Servico/ns2:CodigoTributacaoMunicipio', ns_giss)
    data['CodigoMunicipioServico'] = _get_text_or_none(declaracao_prestacao_servico, 'ns2:Servico/ns2:CodigoMunicipio', ns_giss)

    # Valores do Serviço (priorizando os valores detalhados de DeclaracaoPrestacaoServico/Servico/Valores)
    data['ValorServicos'] = _get_text_or_none(servico_values, 'ns2:ValorServicos', ns_giss)
    data['ValorDeducoes'] = _get_text_or_none(servico_values, 'ns2:ValorDeducoes', ns_giss)
    data['ValorPis'] = _get_text_or_none(servico_values, 'ns2:ValorPis', ns_giss)
    data['ValorCofins'] = _get_text_or_none(servico_values, 'ns2:ValorCofins', ns_giss)
    data['ValorInss'] = _get_text_or_none(servico_values, 'ns2:ValorInss', ns_giss)
    data['ValorIr'] = _get_text_or_none(servico_values, 'ns2:ValorIr', ns_giss)
    data['ValorCsll'] = _get_text_or_none(servico_values, 'ns2:ValorCsll', ns_giss)
    
    iss_retido_code = _get_text_or_none(declaracao_prestacao_servico, 'ns2:Servico/ns2:IssRetido', ns_giss)
    data['IssRetido'] = iss_retido_code # Código 1=Sim, 2=Não
    
    valor_iss_from_service = _get_text_or_none(servico_values, 'ns2:ValorIss', ns_giss)
    data['ValorIss'] = valor_iss_from_service
    
    data['ValorIssRetido'] = valor_iss_from_service if iss_retido_code == '1' else '0.0' 

    data['OutrasRetencoes'] = _get_text_or_none(servico_values, 'ns2:OutrasRetencoes', ns_giss)
    
    # BaseCalculo está em ns2:InfNfse/ns2:ValoresNfse/ns2:BaseCalculo
    base_calculo_infnfse = _get_text_or_none(inf_nfse, 'ns2:ValoresNfse/ns2:BaseCalculo', ns_giss)
    # Aliquota também aparece em ns2:InfNfse/ns2:ValoresNfse/ns2:Aliquota
    aliquota_infnfse = _get_text_or_none(inf_nfse, 'ns2:ValoresNfse/ns2:Aliquota', ns_giss)

    # Usar a base de cálculo da NFSe se a do serviço não estiver presente (ou vice-versa)
    # Neste XML, BaseCalculo está em inf_nfse/ValoresNfse
    data['BaseCalculo'] = base_calculo_infnfse
    
    # Priorizar Alíquota do serviço, mas usar a da NFSe como fallback
    data['Aliquota'] = _get_text_or_none(servico_values, 'ns2:Aliquota', ns_giss)
    if not data['Aliquota'] and aliquota_infnfse:
        data['Aliquota'] = aliquota_infnfse

    data['ValorLiquidoNfse'] = _get_text_or_none(inf_nfse, 'ns2:ValoresNfse/ns2:ValorLiquidoNfse', ns_giss)
    data['DescontoIncondicionado'] = _get_text_or_none(servico_values, 'ns2:DescontoIncondicionado', ns_giss)
    data['DescontoCondicionado'] = _get_text_or_none(servico_values, 'ns2:DescontoCondicionado', ns_giss)

    # Prestador
    # O elemento Prestador está sob InfDeclaracaoPrestacaoServico
    prestador_info_from_declaracao = declaracao_prestacao_servico.find('ns2:Prestador', ns_giss)
    # PrestadorServico (que contém Endereço e Contato) está sob InfNfse
    prestador_servico_info = inf_nfse.find('ns2:PrestadorServico', ns_giss)

    prestador_cnpj_cpf_node = prestador_info_from_declaracao.find('ns2:CpfCnpj', ns_giss) if prestador_info_from_declaracao else None
    cnpj_prestador = _get_text_or_none(prestador_cnpj_cpf_node, 'ns2:Cnpj', ns_giss)
    cpf_prestador = _get_text_or_none(prestador_cnpj_cpf_node, 'ns2:Cpf', ns_giss)
    data['Prestador.CpfCnpj'] = _clean_cnpj_cpf(cnpj_prestador if cnpj_prestador else cpf_prestador)

    data['Prestador.InscricaoMunicipal'] = _get_text_or_none(prestador_info_from_declaracao, 'ns2:InscricaoMunicipal', ns_giss)
    data['Prestador.RazaoSocial'] = _get_text_or_none(prestador_servico_info, 'ns2:RazaoSocial', ns_giss)
    
    prestador_endereco_elem = prestador_servico_info.find('ns2:Endereco', ns_giss) if prestador_servico_info else None
    data['Prestador.Endereco.Logradouro'] = _get_text_or_none(prestador_endereco_elem, 'ns2:Endereco', ns_giss)
    data['Prestador.Endereco.Numero'] = _get_text_or_none(prestador_endereco_elem, 'ns2:Numero', ns_giss)
    data['Prestador.Endereco.Complemento'] = _get_text_or_none(prestador_endereco_elem, 'ns2:Complemento', ns_giss)
    data['Prestador.Endereco.Bairro'] = _get_text_or_none(prestador_endereco_elem, 'ns2:Bairro', ns_giss)
    data['Prestador.Endereco.CodigoMunicipio'] = _get_text_or_none(prestador_endereco_elem, 'ns2:CodigoMunicipio', ns_giss)
    data['Prestador.Endereco.Uf'] = _get_text_or_none(prestador_endereco_elem, 'ns2:Uf', ns_giss)
    data['Prestador.Endereco.Cep'] = _get_text_or_none(prestador_endereco_elem, 'ns2:Cep', ns_giss)
    
    prestador_contato_elem = prestador_servico_info.find('ns2:Contato', ns_giss) if prestador_servico_info else None
    data['Prestador.Contato.Telefone'] = _get_text_or_none(prestador_contato_elem, 'ns2:Telefone', ns_giss)
    data['Prestador.Contato.Email'] = _get_text_or_none(prestador_contato_elem, 'ns2:Email', ns_giss)

    # Tomador
    # O elemento TomadorServico está sob InfDeclaracaoPrestacaoServico
    tomador_servico_info = declaracao_prestacao_servico.find('ns2:TomadorServico', ns_giss)
    
    tomador_cnpj_cpf_node = tomador_servico_info.find('ns2:IdentificacaoTomador/ns2:CpfCnpj', ns_giss) if tomador_servico_info else None
    cnpj_tomador = _get_text_or_none(tomador_cnpj_cpf_node, 'ns2:Cnpj', ns_giss)
    cpf_tomador = _get_text_or_none(tomador_cnpj_cpf_node, 'ns2:Cpf', ns_giss)
    data['TomadorServico.CpfCnpj'] = _clean_cnpj_cpf(cnpj_tomador if cnpj_tomador else cpf_tomador)

    data['TomadorServico.RazaoSocial'] = _get_text_or_none(tomador_servico_info, 'ns2:RazaoSocial', ns_giss)
    
    tomador_endereco_elem = tomador_servico_info.find('ns2:Endereco', ns_giss) if tomador_servico_info else None
    data['TomadorServico.Endereco.Logradouro'] = _get_text_or_none(tomador_endereco_elem, 'ns2:Endereco', ns_giss)
    data['TomadorServico.Endereco.Numero'] = _get_text_or_none(tomador_endereco_elem, 'ns2:Numero', ns_giss)
    data['TomadorServico.Endereco.Bairro'] = _get_text_or_none(tomador_endereco_elem, 'ns2:Bairro', ns_giss)
    data['TomadorServico.Endereco.CodigoMunicipio'] = _get_text_or_none(tomador_endereco_elem, 'ns2:CodigoMunicipio', ns_giss)
    data['TomadorServico.Endereco.Uf'] = _get_text_or_none(tomador_endereco_elem, 'ns2:Uf', ns_giss)
    data['TomadorServico.Endereco.Cep'] = _get_text_or_none(tomador_endereco_elem, 'ns2:Cep', ns_giss)
    
    tomador_contato_elem = tomador_servico_info.find('ns2:Contato', ns_giss) if tomador_servico_info else None
    data['TomadorServico.Contato.Telefone'] = _get_text_or_none(tomador_contato_elem, 'ns2:Telefone', ns_giss)

    # Órgão Gerador
    orgao_gerador_info = inf_nfse.find('ns2:OrgaoGerador', ns_giss)
    data['OrgaoGerador.CodigoMunicipio'] = _get_text_or_none(orgao_gerador_info, 'ns2:CodigoMunicipio', ns_giss)
    data['OrgaoGerador.Uf'] = _get_text_or_none(orgao_gerador_info, 'ns2:Uf', ns_giss)


    # --- Adicionado para depuração ---
    print("\nDEBUG GISS EXTRACTED VALUES (AFTER CORRECTION):")
    print(f"  Nfse.Id: {data['Nfse.Id']}")
    print(f"  Numero: {data['Numero']}")
    print(f"  DataEmissao: {data['DataEmissao']}")
    print(f"  OptanteSimplesNacional: {data['OptanteSimplesNacional']}")
    print(f"  ValorServicos: {data['ValorServicos']}")
    print(f"  ValorDeducoes: {data['ValorDeducoes']}")
    print(f"  ValorPis: {data['ValorPis']}")
    print(f"  ValorCofins: {data['ValorCofins']}")
    print(f"  ValorInss: {data['ValorInss']}")
    print(f"  ValorIr: {data['ValorIr']}")
    print(f"  ValorCsll: {data['ValorCsll']}")
    print(f"  IssRetido (code): {data['IssRetido']}")
    print(f"  ValorIss: {data['ValorIss']}")
    print(f"  ValorIssRetido: {data['ValorIssRetido']}")
    print(f"  BaseCalculo: {data['BaseCalculo']}")
    print(f"  Aliquota: {data['Aliquota']}")
    print(f"  ValorLiquidoNfse: {data['ValorLiquidoNfse']}")
    print(f"  DescontoIncondicionado: {data['DescontoIncondicionado']}")
    print(f"  DescontoCondicionado: {data['DescontoCondicionado']}")
    print(f"  Prestador.CpfCnpj: {data['Prestador.CpfCnpj']}")
    print(f"  Prestador.RazaoSocial: {data['Prestador.RazaoSocial']}")
    print(f"  TomadorServico.CpfCnpj: {data['TomadorServico.CpfCnpj']}")
    print(f"  TomadorServico.RazaoSocial: {data['TomadorServico.RazaoSocial']}")
    # --- Fim dos prints de depuração ---


    # --- Verificação de Cancelamento para GISS ---
    nfse_cancelamento = root.find('.//ns2:NfseCancelamento', ns_giss)
    if nfse_cancelamento is not None:
        data['IsCancelled'] = 'Sim'
        # Atualiza os campos conforme solicitado para notas canceladas
        data['TomadorServico.RazaoSocial'] = 'CANCELADA'
        data['DescricaoServico'] = 'NOTA FISCAL CANCELADA'
        data['TomadorServico.CpfCnpj'] = None # Limpa CPF/CNPJ do tomador
        data['TomadorServico.Endereco.Logradouro'] = None
        data['TomadorServico.Endereco.Numero'] = None
        data['TomadorServico.Endereco.Complemento'] = None
        data['TomadorServico.Endereco.Bairro'] = None
        data['TomadorServico.Endereco.CodigoMunicipio'] = None
        data['TomadorServico.Endereco.Uf'] = None
        data['TomadorServico.Endereco.Cep'] = None
        data['TomadorServico.Contato.Telefone'] = None

        # Zera todos os valores financeiros para notas canceladas
        for key in ['ValorServicos', 'ValorDeducoes', 'ValorPis', 'ValorCofins', 'ValorInss', 'ValorIr', 'ValorCsll',
                    'ValorIss', 'ValorIssRetido', 'OutrasRetencoes', 'BaseCalculo', 'Aliquota', 'ValorLiquidoNfse',
                    'DescontoIncondicionado', 'DescontoCondicionado']:
            data[key] = '0.0' # Define como string '0.0' para ser convertido para float 0.0 posteriormente
    else:
        data['IsCancelled'] = 'Não'

    return data

# --- Parser Específico para o Layout GINFES ---
# ... (manter o código _parse_ginfes_nfse inalterado) ...
def _parse_ginfes_nfse(root, xml_file_path):
    """
    Extrai dados de NFSe no layout GINFES, baseado no seu script original,
    assumindo que os elementos internos estão no "empty namespace".
    """
    data = _DEFAULT_NFSE_DATA.copy()

    lista_nfse = root.find('ListaNfse')
    if lista_nfse is None:
        return data

    comp_nfse = lista_nfse.find('CompNfse')
    if comp_nfse is None:
        return data

    nfse_element = comp_nfse.find('Nfse')
    if nfse_element is None:
        return data

    inf_nfse_element = nfse_element.find('InfNfse')
    if inf_nfse_element is None:
        return data

    # --- Extração dos Dados a partir de <InfNfse> ---
    data['Nfse.Id'] = _get_attr_or_none(inf_nfse_element, '.', 'Id')
    data['Numero'] = _get_text_or_none(inf_nfse_element, 'Numero')
    data['CodigoVerificacao'] = _get_text_or_none(inf_nfse_element, 'CodigoVerificacao')
    data['DataEmissao'] = _get_text_or_none(inf_nfse_element, 'DataEmissao')
    data['NaturezaOperacao'] = _get_text_or_none(inf_nfse_element, 'NaturezaOperacao')
    data['RegimeEspecialTributacao'] = _get_text_or_none(inf_nfse_element, 'RegimeEspecialTributacao')
    data['OptanteSimplesNacional'] = _get_text_or_none(inf_nfse_element, 'OptanteSimplesNacional')
    data['IncentivadorCultural'] = _get_text_or_none(inf_nfse_element, 'IncentivadorCultural')

    # Dados do Serviço
    servico_element = inf_nfse_element.find('Servico')
    if servico_element is not None:
        data['DescricaoServico'] = _get_text_or_none(servico_element, 'Discriminacao')
        data['ItemListaServico'] = _get_text_or_none(servico_element, 'ItemListaServico')
        data['CodigoTributacaoMunicipio'] = _get_text_or_none(servico_element, 'CodigoTributacaoMunicipio')
        data['CodigoMunicipioServico'] = _get_text_or_none(servico_element, 'CodigoMunicipio')
        
        valores_servico = servico_element.find('Valores')
        if valores_servico is not None:
            data['ValorServicos'] = _get_text_or_none(valores_servico, 'ValorServicos')
            data['ValorDeducoes'] = _get_text_or_none(valores_servico, 'ValorDeducoes')
            data['ValorPis'] = _get_text_or_none(valores_servico, 'ValorPis')
            data['ValorCofins'] = _get_text_or_none(valores_servico, 'ValorCofins')
            data['ValorInss'] = _get_text_or_none(valores_servico, 'ValorInss')
            data['ValorIr'] = _get_text_or_none(valores_servico, 'ValorIr')
            data['ValorCsll'] = _get_text_or_none(valores_servico, 'ValorCsll')
            data['IssRetido'] = _get_text_or_none(valores_servico, 'IssRetido') # Código de retenção
            data['ValorIss'] = _get_text_or_none(valores_servico, 'ValorIss')
            data['ValorIssRetido'] = _get_text_or_none(valores_servico, 'ValorIssRetido')
            data['OutrasRetencoes'] = _get_text_or_none(valores_servico, 'OutrasRetencoes')
            data['BaseCalculo'] = _get_text_or_none(valores_servico, 'BaseCalculo')
            data['Aliquota'] = _get_text_or_none(valores_servico, 'Aliquota')
            data['ValorLiquidoNfse'] = _get_text_or_none(valores_servico, 'ValorLiquidoNfse')
            data['DescontoIncondicionado'] = _get_text_or_none(valores_servico, 'DescontoIncondicionado')
            data['DescontoCondicionado'] = _get_text_or_none(valores_servico, 'DescontoCondicionado')
    

    # Dados do Prestador de Serviços
    prestador_element = inf_nfse_element.find('PrestadorServico')
    if prestador_element is not None:
        identificacao_prestador = prestador_element.find('IdentificacaoPrestador')
        if identificacao_prestador is not None:
            cnpj_prestador = _get_text_or_none(identificacao_prestador, 'Cnpj')
            cpf_prestador = _get_text_or_none(identificacao_prestador, 'Cpf')
            data['Prestador.CpfCnpj'] = _clean_cnpj_cpf(cnpj_prestador if cnpj_prestador else cpf_prestador)
            data['Prestador.InscricaoMunicipal'] = _get_text_or_none(identificacao_prestador, 'InscricaoMunicipal')
        
        data['Prestador.RazaoSocial'] = _get_text_or_none(prestador_element, 'RazaoSocial')
        
        endereco_prestador = prestador_element.find('Endereco')
        if endereco_prestador is not None:
            data['Prestador.Endereco.Logradouro'] = _get_text_or_none(endereco_prestador, 'Endereco') # Tag Endereco é o nome da rua
            data['Prestador.Endereco.Numero'] = _get_text_or_none(endereco_prestador, 'Numero')
            data['Prestador.Endereco.Complemento'] = _get_text_or_none(endereco_prestador, 'Complemento')
            data['Prestador.Endereco.Bairro'] = _get_text_or_none(endereco_prestador, 'Bairro')
            data['Prestador.Endereco.CodigoMunicipio'] = _get_text_or_none(endereco_prestador, 'CodigoMunicipio')
            data['Prestador.Endereco.Uf'] = _get_text_or_none(endereco_prestador, 'Uf')
            data['Prestador.Endereco.Cep'] = _get_text_or_none(endereco_prestador, 'Cep')

        contato_prestador = prestador_element.find('Contato')
        if contato_prestador is not None:
            data['Prestador.Contato.Telefone'] = _get_text_or_none(contato_prestador, 'Telefone')
            data['Prestador.Contato.Email'] = _get_text_or_none(contato_prestador, 'Email')


    # Dados do Tomador de Serviços
    tomador_element = inf_nfse_element.find('TomadorServico')
    if tomador_element is not None:
        identificacao_tomador = tomador_element.find('IdentificacaoTomador')
        if identificacao_tomador is not None:
            cpf_cnpj_tomador = identificacao_tomador.find('CpfCnpj')
            if cpf_cnpj_tomador is not None:
                cnpj_tomador = _get_text_or_none(cpf_cnpj_tomador, 'Cnpj')
                cpf_tomador = _get_text_or_none(cpf_cnpj_tomador, 'Cpf')
                data['TomadorServico.CpfCnpj'] = _clean_cnpj_cpf(cnpj_tomador if cnpj_tomador else cpf_tomador)
            
        data['TomadorServico.RazaoSocial'] = _get_text_or_none(tomador_element, 'RazaoSocial')
        
        endereco_tomador = tomador_element.find('Endereco')
        if endereco_tomador is not None:
            data['TomadorServico.Endereco.Logradouro'] = _get_text_or_none(endereco_tomador, 'Endereco')
            data['TomadorServico.Endereco.Numero'] = _get_text_or_none(endereco_tomador, 'Numero')
            data['TomadorServico.Endereco.Bairro'] = _get_text_or_none(endereco_tomador, 'Bairro')
            data['TomadorServico.Endereco.CodigoMunicipio'] = _get_text_or_none(endereco_tomador, 'CodigoMunicipio')
            data['TomadorServico.Endereco.Uf'] = _get_text_or_none(endereco_tomador, 'Uf')
            data['TomadorServico.Endereco.Cep'] = _get_text_or_none(endereco_tomador, 'Cep')

        contato_tomador = tomador_element.find('Contato')
        if contato_tomador is not None:
            data['TomadorServico.Contato.Telefone'] = _get_text_or_none(contato_tomador, 'Telefone')

    # Dados do Órgão Gerador
    orgao_gerador_element = inf_nfse_element.find('OrgaoGerador')
    if orgao_gerador_element is not None:
        data['OrgaoGerador.CodigoMunicipio'] = _get_text_or_none(orgao_gerador_element, 'CodigoMunicipio')
        data['OrgaoGerador.Uf'] = _get_text_or_none(orgao_gerador_element, 'Uf')

    # --- Verificação de Cancelamento para GINFES ---
    # Para GINFES, assume que não é cancelada se não houver um campo de status específico.
    # Se o seu XML GINFES tiver um indicador de cancelamento, esta parte precisa ser atualizada.
    # Exemplo: Se houver uma tag <NfseCancelada> ou um atributo 'status'='CANCELADA' em algum lugar.
    # Por enquanto, mantemos como 'Não' por padrão.
    # Adicionei uma busca por um bloco <CancelamentoNfse> na raiz do documento ou similar,
    # que é um padrão comum em alguns modelos GINFES para cancelamento.
    cancelamento_ginfes = root.find('.//CancelamentoNfse') 
    if cancelamento_ginfes is not None:
        data['IsCancelled'] = 'Sim'
        # Zera todos os valores financeiros para notas canceladas GINFES
        for key in ['ValorServicos', 'ValorDeducoes', 'ValorPis', 'ValorCofins', 'ValorInss', 'ValorIr', 'ValorCsll',
                    'ValorIss', 'ValorIssRetido', 'OutrasRetencoes', 'BaseCalculo', 'Aliquota', 'ValorLiquidoNfse',
                    'DescontoIncondicionado', 'DescontoCondicionado']:
            data[key] = '0.0' # Define como string '0.0' para ser convertido para float 0.0 posteriormente
        data['TomadorServico.RazaoSocial'] = 'CANCELADA'
        data['DescricaoServico'] = 'NOTA FISCAL CANCELADA'
        # Outros campos do tomador podem ser zerados ou marcados como None se desejado.
    else:
        data['IsCancelled'] = 'Não'

    return data

# --- Função principal de extração de dados da NFSe ---
def extract_nfse_data(xml_file_path):
    """
    Função principal para extrair dados de um arquivo XML de NFSe.
    Detecta automaticamente o formato do XML (GISS ou GINFES) e usa o parser apropriado.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # Define o namespace URI para o formato GISS
        giss_namespace_uri = 'http://www.giss.com.br/tipos-v2_04.xsd'
        
        # 1. Tenta detectar o formato GISS (verifica a tag raiz e o namespace)
        if root.tag == '{' + giss_namespace_uri + '}CompNfse':
            print(f"Detectado formato GISS para {os.path.basename(xml_file_path)}")
            return _parse_giss_nfse(root)
        
        # 2. Tenta detectar o formato GINFES (verifica a presença de 'ListaNfse' na raiz ou em primeiro nível)
        # Mais robusto para GINFES: verifica tags comuns na raiz ou sub-raízes
        if root.tag in ['ConsultarNfseResposta', 'GerarNfseResposta', 'PedidoCancelamentoNFSeEnvio'] or root.find('ListaNfse') is not None:
            print(f"Detectado formato GINFES para {os.path.basename(xml_file_path)}")
            return _parse_ginfes_nfse(root, xml_file_path)
        
        # 3. Se nenhum formato conhecido for detectado
        print(f"Formato XML desconhecido ou não suportado para {os.path.basename(xml_file_path)}")
        return _DEFAULT_NFSE_DATA.copy() # Retorna dados padrão

    except ET.ParseError as e:
        print(f"ERRO: Falha ao fazer o parsing do XML '{os.path.basename(xml_file_path)}': {e}")
        return _DEFAULT_NFSE_DATA.copy() # Retorna dados padrão em caso de erro de parsing
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado ao processar '{os.path.basename(xml_file_path)}': {e}")
        return _DEFAULT_NFSE_DATA.copy() # Retorna dados padrão em caso de erro inesperado