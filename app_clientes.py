import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import re

# ——————————————————————————————
#  VERIFICAÇÃO PING UPTIMEROBOT (MELHORADA)
# ——————————————————————————————
# Verifica se é uma requisição do UptimeRobot antes de qualquer coisa
if 'QUERY_STRING' in os.environ and 'ping=1' in os.environ['QUERY_STRING']:
    print("ok")
    exit(0)

# ——————————————————————————————
#  CONFIGURAÇÃO DA PÁGINA
# ——————————————————————————————
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# ——————————————————————————————
#  VERIFICAÇÃO ALTERNATIVA
# ——————————————————————————————
# Verificação adicional para garantir
try:
    params = st.query_params
    if params.get("ping") == "1":
        st.write("ok")
        st.stop()
except:
    pass

# ——————————————————————————————
#  LISTA DE EMAILS AUTORIZADOS
# ——————————————————————————————
EMAILS_AUTORIZADOS = {
    "nardie.arruda@normaq.com.br",
    "tarcio.henrique@normaq.com.br",
    "camila.aguiar@normaq.com.br",
    "sergio.carvalho@normaq.com.br",
    "flavia.costa@normaq.com.br",
    "johnny.barbosa@normaq.com.br",
    "joao.victor@normaq.com.br",
    "alison.ferreira@normaq.com.br",
    "thiago.carmo@normaq.com.br",
    "antonio.gustavo@normaq.com.br",
    "raony.lins@normaq.com.br",
    "graziela.galdino@normaq.com.br"
}

# ——————————————————————————————
#  VERIFICAÇÃO DE EMAIL
# ——————————————————————————————
def verificar_email():
    if 'email_verificado' not in st.session_state:
        st.session_state.email_verificado = False
    
    if not st.session_state.email_verificado:
        st.title("🔍 Carteira de Clientes NORMAQ JCB")
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("🔐 Acesso Restrito")
            email = st.text_input("Digite seu email corporativo:", placeholder="seu.email@normaq.com.br")
            
            if st.button("Acessar Sistema", type="primary", use_container_width=True):
                if email.lower() in EMAILS_AUTORIZADOS:
                    st.session_state.email_verificado = True
                    st.session_state.email_usuario = email.lower()
                    st.success("Acesso permitido!")
                    st.rerun()
                else:
                    st.error("Email não autorizado. Entre em contato com o administrador.")
        
        st.markdown("---")
        st.info("📧 Apenas emails corporativos autorizados têm acesso a este sistema")
        st.stop()

# ——————————————————————————————
#  FUNÇÃO DE CREDENCIAIS
# ——————————————————————————————
def get_google_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_config = st.secrets.gcp_service_account
    return Credentials.from_service_account_info(creds_config, scopes=scopes)

# ——————————————————————————————
#  FUNÇÃO PARA CARREGAR PLANILHAS
# ——————————————————————————————
def load_sheet_data(client, spreadsheet_url, sheet_name):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    records = worksheet.get_all_records()
    if not records:
        return None
    df = pd.DataFrame(records).dropna(how="all")
    # Manter os nomes originais das colunas
    df.columns = [str(c).strip() for c in df.columns]
    return df

# ——————————————————————————————
#  FUNÇÃO PARA OBTER CABEÇALHOS EXATOS
# ——————————————————————————————
def get_exact_headers(client, spreadsheet_url, sheet_name):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    headers = worksheet.row_values(1)
    return [str(header).strip() for header in headers]

# ——————————————————————————————
#  FUNÇÃO PARA SALVAR DADOS NA PLANILHA
# ——————————————————————————————
def save_to_sheet(client, spreadsheet_url, sheet_name, data):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    
    # Obter cabeçalhos existentes
    headers = get_exact_headers(client, spreadsheet_url, sheet_name)
    
    # Preparar dados para inserção
    row_data = []
    for header in headers:
        # Encontrar correspondência case-insensitive
        found = False
        for data_key in data.keys():
            if data_key.upper() == header.upper():
                row_data.append(data[data_key])
                found = True
                break
        if not found:
            row_data.append("")
    
    # Adicionar nova linha
    worksheet.append_row(row_data)
    return True

# ——————————————————————————————
#  FUNÇÃO PARA ATUALIZAR DADOS NA PLANILHA
# ——————————————————————————————
def update_sheet_data(client, spreadsheet_url, sheet_name, row_index, data):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    
    # Obter cabeçalhos exatos
    headers = get_exact_headers(client, spreadsheet_url, sheet_name)
    
    # Preparar dados para atualização
    for data_key, value in data.items():
        # Encontrar correspondência case-insensitive
        col_index = None
        for i, header in enumerate(headers):
            if data_key.upper() == header.upper():
                col_index = i + 1
                break
        
        if col_index:
            worksheet.update_cell(row_index, col_index, value)
        else:
            st.warning(f"Coluna '{data_key}' não encontrada na planilha.")
    
    return True

# ——————————————————————————————
#  FUNÇÃO FLEXÍVEL PARA PEGAR VALORES
# ——————————————————————————————
def get_value(row, col_name, default="Não informado"):
    for col in row.index:
        if col.strip().upper() == col_name.upper():
            return row[col] if row[col] not in [None, ""] else default
    return default

# ——————————————————————————————
#  FUNÇÃO PARA FORMATAR NÚMERO DE TELEFONE
# ——————————————————————————————
def formatar_telefone(telefone):
    if not telefone or telefone == "Não informado":
        return telefone
    
    # Remover caracteres não numéricos
    numeros = re.sub(r'\D', '', str(telefone))
    
    # Formatar número para WhatsApp (55DDDNUMERO)
    if numeros.startswith('55') and len(numeros) >= 12:
        return numeros
    elif len(numeros) == 11:  # Com DDD (11 dígitos)
        return '55' + numeros
    elif len(numeros) == 10:  # Com DDD (10 dígitos)
        return '55' + numeros
    else:
        return numeros  # Retorna como está se não conseguir formatar

# ——————————————————————————————
#  FUNÇÃO PARA CRIAR TABELA HTML PROTEGIDA
# ——————————————————————————————
def criar_tabela_html_protegida(dataframe):
    """Cria uma tabela HTML protegida contra download e cópia"""
    
    # Converter DataFrame para HTML
    html = dataframe.to_html(index=False, escape=False, classes='protected-table')
    
    # Adicionar proteção CSS
    protected_html = f"""
    <style>
    .protected-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 14px;
        text-align: center;
        background-color: white;
    }}
    .protected-table th {{
        background-color: #f0f0f0;
        padding: 12px;
        border: 2px solid #ddd;
        font-weight: bold;
        color: #333;
    }}
    .protected-table td {{
        padding: 10px;
        border: 1px solid #ddd;
        color: #333;
    }}
    .protected-table tr:nth-child(even) {{
        background-color: #f9f9f9;
    }}
    .protected-table tr:hover {{
        background-color: #f5f5f5;
    }}
    .table-protector {{
        position: relative;
        overflow-x: auto;
        margin: 20px 0;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        background-color: white;
    }}
    .table-protector::after {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: transparent;
        z-index: 9999;
        cursor: not-allowed;
    }}
    /* Esconder completamente qualquer botão de download */
    .stDownloadButton, [data-testid="stDownloadButton"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    /* Bloquear completamente seleção de texto */
    body {{
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        user-select: none !important;
    }}
    /* Permitir seleção apenas em campos de entrada */
    input, textarea {{
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
        user-select: text !important;
    }}
    /* Remover qualquer menu de contexto */
    body {{
        context-menu: none !important;
    }}
    </style>
    
    <div class="table-protector">
        {html}
    </div>
    """
    
    return protected_html

# ——————————————————————————————
#  INTERFACE PRINCIPAL
# ——————————————————————————————
def main():
    # Verificar email antes de mostrar qualquer conteúdo
    verificar_email()
    
    # Mostrar email do usuário logado
    st.sidebar.success(f"👤 Logado como: {st.session_state.email_usuario}")
    
    if st.sidebar.button("🚪 Sair"):
        st.session_state.email_verificado = False
        st.session_state.email_usuario = None
        st.rerun()

    st.title("🔍 Carteira de Clientes NORMAQ JCB")

    # Adicionar abas
    tab1, tab2, tab3 = st.tabs(["Consulta", "Cadastro de Cliente", "Ajuste de Cliente"])
    
    with tab1:
        try:
            creds = get_google_creds()
            client = gspread.authorize(creds)

            SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1sresryYLTR8aCp2ZCR82kfQKaUrqLxeFBVpVI2Yw7_I/edit?usp=sharing"

            @st.cache_data(ttl=3600)
            def get_data(sheet):
                return load_sheet_data(client, SPREADSHEET_URL, sheet)

            df_pagina1 = get_data("Página1")
            df_pagina2 = get_data("Página2")

            if df_pagina1 is None or df_pagina1.empty:
                st.warning("Nenhum dado disponível na Página1")
                return

            # Adicionar opção de consulta por CNPJ/CPF
            consulta_por = st.radio("Consultar por:", ["Cliente", "CNPJ/CPF"], horizontal=True)
            
            if consulta_por == "Cliente":
                # Converter para string para evitar erro de comparação
                clientes_disponiveis = sorted([str(cliente) for cliente in df_pagina1["CLIENTES"].dropna().unique()])
                cliente_selecionado = st.selectbox("Selecione um cliente:", clientes_disponiveis, key="cliente_select")
                cliente_data = df_pagina1[df_pagina1["CLIENTES"].astype(str) == cliente_selecionado]
            else:
                # Converter CNPJ/CPF para string para evitar erro de comparação
                cnpj_cpf_disponiveis = sorted([str(cnpj) for cnpj in df_pagina1["CNPJ/CPF"].dropna().unique()])
                cnpj_cpf_selecionado = st.selectbox("Selecione um CNPJ/CPF:", cnpj_cpf_disponiveis, key="cnpj_select")
                cliente_data = df_pagina1[df_pagina1["CNPJ/CPF"].astype(str) == cnpj_cpf_selecionado]
                cliente_selecionado = get_value(cliente_data.iloc[0], "CLIENTES") if not cliente_data.empty else ""

            if not cliente_data.empty:
                row = cliente_data.iloc[0]

                # Obter e formatar número de contato para WhatsApp
                contato_value = get_value(row, "Contato")
                telefone_formatado = formatar_telefone(contato_value)
                whatsapp_link = f"https://wa.me/{telefone_formatado}" if telefone_formatado and telefone_formatado != "Não informado" else "#"

                # CARD DE INFORMAÇÕES
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(
                        f"""
                        <div style='
                            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
                            border-radius: 12px;
                            padding: 20px;
                            margin: 15px 0;
                            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
                            color: white;
                            border-left: 4px solid #4CAF50;
                        '>
                            <p style='font-size:16px; margin: 10px 0; line-height: 1.4;'>
                                <strong style='color:#4CAF50; font-size:14px;'>👤 CONSULTOR:</strong><br>
                                <span style='font-size:18px; font-weight:600;'>{get_value(row, "NOVO CONSULTOR")}</span>
                            </p>
                            <hr style='border: 0.5px solid #444; margin: 15px 0;'>
                            <p style='font-size:16px; margin: 10px 0; line-height: 1.4;'>
                                <strong style='color:#2196F3; font-size:14px;'>🏢 REVENDA:</strong><br>
                                <span style='font-size:18px; font-weight:600;'>{get_value(row, "Revenda")}</span>
                            </p>
                            <hr style='border: 0.5px solid #444; margin: 15px 0;'>
                            <p style='font-size:16px; margin: 10px 0; line-height: 1.4;'>
                                <strong style='color:#FF9800; font-size:14px;'>🔧 PSSR:</strong><br>
                                <span style='font-size:18px; font-weight:600;'>{get_value(row, "PSSR")}</span>
                            </p>
                            <hr style='border: 0.5px solid #444; margin: 15px 0;'>
                            <p style='font-size:16px; margin: 10px 0; line-height: 1.4;'>
                                <strong style='color:#9C27B0; font-size:14px;'>📞 CONTATO:</strong><br>
                                <span style='font-size:18px; font-weight:600;'>
                                    <a href='{whatsapp_link}' target='_blank' style='color: #25D366; text-decoration: none;'>
                                        {contato_value} 💬
                                    </a>
                                </span>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    if df_pagina2 is not None and not df_pagina2.empty:
                        maquinas_cliente = df_pagina2[df_pagina2["CLIENTES"].astype(str) == cliente_selecionado]

                        if not maquinas_cliente.empty:
                            qtd_maquinas = len(maquinas_cliente)
                            
                            # Calcular total por categoria
                            categorias_count = maquinas_cliente["CATEGORIA"].value_counts()
                            categorias_str = " | ".join([f"{cat} - {count:02d}" for cat, count in categorias_count.items()])

                            # Mensagem com destaque
                            st.markdown(
                                f"""
                                <div style='
                                    background: #f8f9fa;
                                    padding: 10px 15px;
                                    border-radius: 10px;
                                    margin-bottom: 10px;
                                    font-size: 16px;
                                    color: #333;
                                    border: 1px solid #ddd;
                                '>
                                💡 Selecione um cliente para visualizar as informações completas
                                <span style="font-weight:bold; font-size:18px; color:#4CAF50;">
                                    - Quantidade de Máquinas: {qtd_maquinas}
                                </span>
                                <br>
                                <span style="font-weight:bold; font-size:16px; color:#2196F3;">
                                    Categorias: {categorias_str}
                                </span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Ajuste da coluna SERIE para remover pontos/virgulas
                            maquinas_cliente["SERIE"] = maquinas_cliente["SERIE"].astype(str).str.replace(r"[.,]", "", regex=True)

                            # Adicionar número sequencial (começando em 1)
                            maquinas_cliente = maquinas_cliente.copy()
                            maquinas_cliente["N°"] = range(1, len(maquinas_cliente) + 1)
                            
                            # Adicionar coluna Nº CLIENTE da Página1 e remover vírgulas
                            n_cliente_value = get_value(row, "Nº Cliente", "")
                            # Remover vírgulas e caracteres não numéricos, mantendo apenas números
                            n_cliente_limpo = re.sub(r'[^\d]', '', str(n_cliente_value))
                            maquinas_cliente["Nº CLIENTE"] = n_cliente_limpo
                            
                            # Reordenar colunas: N°, Nº CLIENTE, CLIENTES, depois as demais
                            cols_ordenadas = ["N°", "Nº CLIENTE", "CLIENTES"] + [col for col in maquinas_cliente.columns if col not in ["N°", "Nº CLIENTE", "CLIENTES"]]
                            maquinas_cliente = maquinas_cliente[cols_ordenadas]

                            # Remover colunas vazias ou sem nome (incluindo a primeira coluna sem nome)
                            maquinas_cliente = maquinas_cliente.loc[:, ~maquinas_cliente.columns.str.contains('^Unnamed', na=False)]
                            maquinas_cliente = maquinas_cliente.loc[:, maquinas_cliente.columns != '']
                            # Remover a primeira coluna se estiver vazia (índice antigo)
                            if maquinas_cliente.iloc[:, 0].name == 'N°':
                                # Já está correto, não fazer nada
                                pass
                            else:
                                # Remover a primeira coluna se não for a coluna N°
                                maquinas_cliente = maquinas_cliente.iloc[:, 1:]

                            # Ajuste dos cabeçalhos (Primeira letra maiúscula)
                            maquinas_cliente.columns = [col.capitalize() for col in maquinas_cliente.columns]

                            # Exibir tabela protegida usando HTML
                            tabela_html = criar_tabela_html_protegida(maquinas_cliente.reset_index(drop=True))
                            st.markdown(tabela_html, unsafe_allow_html=True)
                            
                        else:
                            st.info("💡 Selecione um cliente para visualizar as informações completas")
                            st.warning("📭 Nenhuma máquina encontrada para este cliente")
                    else:
                        st.info("💡 Selecione um cliente para visualizar as informações completas")
            else:
                st.info("👆 Selecione um cliente na lista acima")

        except Exception as e:
            st.error(f"Erro ao carregar a aplicação: {e}")

    with tab2:
        st.header("Cadastro de Novo Cliente")
        
        # Verificar senha
        senha = st.text_input("Digite a senha para acesso:", type="password")
        
        if senha == "NMQ@2025":
            with st.form("form_cadastro"):
                col1, col2 = st.columns(2)
                
                with col1:
                    cliente = st.text_input("CLIENTES*")
                    consultor = st.text_input("NOVO CONSULTOR*")
                    revenda = st.text_input("Revenda*")
                
                with col2:
                    pssr = st.text_input("PSSR*")
                    cnpj_cpf = st.text_input("CNPJ/CPF*")
                    contato = st.text_input("Contato*")
                    n_cliente = st.text_input("Nº Cliente*")
                
                submitted = st.form_submit_button("Cadastrar Cliente")
                
                if submitted:
                    if not all([cliente, consultor, revenda, pssr, cnpj_cpf, contato, n_cliente]):
                        st.error("Todos os campos marcados com * são obrigatórios!")
                    else:
                        try:
                            # Preparar dados com os nomes exatos das colunas
                            novo_cliente = {
                                "CLIENTES": cliente,
                                "NOVO CONSULTOR": consultor,
                                "Revenda": revenda,
                                "PSSR": pssr,
                                "CNPJ/CPF": cnpj_cpf,
                                "Contato": contato,
                                "Nº Cliente": n_cliente
                            }
                            
                            # Salvar na planilha
                            if save_to_sheet(client, SPREADSHEET_URL, "Página1", novo_cliente):
                                st.success("Cliente cadastrado com sucesso!")
                                st.cache_data.clear()
                            else:
                                st.error("Erro ao cadastrar cliente.")
                                
                        except Exception as e:
                            st.error(f"Erro ao cadastrar: {e}")
        elif senha != "":
            st.error("Senha incorreta!")
    
    with tab3:
        st.header("Ajuste de Dados do Cliente")
        
        # Verificar senha
        senha = st.text_input("Digite a senha para acesso:", type="password", key="senha_ajuste")
        
        if senha == "NMQ@2025":
            try:
                # Carregar dados
                df_pagina1 = get_data("Página1")
                
                # Selecionar cliente para ajuste (convertendo para string)
                opcoes_clientes = sorted([str(cliente) for cliente in df_pagina1["CLIENTES"].dropna().unique()])
                cliente_ajuste = st.selectbox("Selecione o cliente para ajuste:", opcoes_clientes)
                
                if cliente_ajuste:
                    # Obter dados do cliente selecionado
                    cliente_data = df_pagina1[df_pagina1["CLIENTES"].astype(str) == cliente_ajuste]
                    
                    if not cliente_data.empty:
                        cliente_data_row = cliente_data.iloc[0]
                        
                        with st.form("form_ajuste"):
                            st.subheader(f"Editando: {cliente_ajuste}")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                novo_cliente = st.text_input("CLIENTES", value=get_value(cliente_data_row, "CLIENTES"))
                                novo_consultor = st.text_input("NOVO CONSULTOR", value=get_value(cliente_data_row, "NOVO CONSULTOR"))
                                nova_revenda = st.text_input("Revenda", value=get_value(cliente_data_row, "Revenda"))
                            
                            with col2:
                                novo_pssr = st.text_input("PSSR", value=get_value(cliente_data_row, "PSSR"))
                                novo_cnpj = st.text_input("CNPJ/CPF", value=get_value(cliente_data_row, "CNPJ/CPF"))
                                novo_contato = st.text_input("Contato", value=get_value(cliente_data_row, "Contato"))
                                novo_n_cliente = st.text_input("Nº Cliente", value=get_value(cliente_data_row, "Nº Cliente"))
                            
                            submitted = st.form_submit_button("Salvar Alterações")
                            
                            if submitted:
                                try:
                                    # Encontrar índice da linha
                                    row_index = cliente_data.index[0] + 2  # +2 porque a planilha tem cabeçalho e índice começa em 1
                                                                    # Preparar dados para atualização (usando os nomes exatos das colunas)
                                    dados_atualizados = {
                                        "CLIENTES": novo_cliente,
                                        "NOVO CONSULTOR": novo_consultor,
                                        "Revenda": nova_revenda,
                                        "PSSR": novo_pssr,
                                        "CNPJ/CPF": novo_cnpj,
                                        "Contato": novo_contato,
                                        "Nº Cliente": novo_n_cliente
                                    }
                                    
                                    # Atualizar na planilha
                                    if update_sheet_data(client, SPREADSHEET_URL, "Página1", row_index, dados_atualizados):
                                        st.success("Dados atualizados com sucesso!")
                                        st.cache_data.clear()
                                    else:
                                        st.error("Erro ao atualizar dados.")
                                        
                                except Exception as e:
                                    st.error(f"Erro ao atualizar: {e}")
                    else:
                        st.warning("Cliente não encontrado!")
                
            except Exception as e:
                st.error(f"Erro ao carregar dados: {e}")
        elif senha != "":
            st.error("Senha incorreta!")

    # Rodapé
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 11px; color: #666; margin-top: 30px;'>
        © {datetime.now().year} NORMAQ JCB - Todos os direitos reservados • 
        Versão 1.4.6 • Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        <br>
        Desenvolvido por Thiago Carmo – Especialista em Dados • 📞 (81) 99514-3900
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
