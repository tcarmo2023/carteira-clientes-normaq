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
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

# ——————————————————————————————
#  FUNÇÃO PARA SALVAR DADOS NA PLANILHA
# ——————————————————————————————
def save_to_sheet(client, spreadsheet_url, sheet_name, data):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    
    # Obter cabeçalhos existentes
    headers = worksheet.row_values(1)
    
    # Preparar dados para inserção
    row_data = []
    for header in headers:
        if header.upper() in data:
            row_data.append(data[header.upper()])
        else:
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
    
    # Obter cabeçalhos
    headers = worksheet.row_values(1)
    
    # Preparar dados para atualização
    for col_name, value in data.items():
        col_index = headers.index(col_name.upper()) + 1
        worksheet.update_cell(row_index, col_index, value)
    
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
#  INTERFACE PRINCIPAL
# ——————————————————————————————
def main():
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
                clientes_disponiveis = sorted(df_pagina1["CLIENTES"].dropna().unique())
                cliente_selecionado = st.selectbox("Selecione um cliente:", clientes_disponiveis, key="cliente_select")
                cliente_data = df_pagina1[df_pagina1["CLIENTES"] == cliente_selecionado]
            else:
                cnpj_cpf_disponiveis = sorted(df_pagina1["CNPJ/CPF"].dropna().unique())
                cnpj_cpf_selecionado = st.selectbox("Selecione um CNPJ/CPF:", cnpj_cpf_disponiveis, key="cnpj_select")
                cliente_data = df_pagina1[df_pagina1["CNPJ/CPF"] == cnpj_cpf_selecionado]
                cliente_selecionado = get_value(cliente_data.iloc[0], "CLIENTES") if not cliente_data.empty else ""

            if not cliente_data.empty:
                row = cliente_data.iloc[0]

                # Obter e formatar número de contato para WhatsApp
                contato_value = get_value(row, "CONTATO")
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
                                <span style='font-size:18px; font-weight:600;'>{get_value(row, "REVENDA")}</span>
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
                        maquinas_cliente = df_pagina2[df_pagina2["CLIENTES"] == cliente_selecionado]

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
                            
                            # Adicionar coluna Nº CLIENTE da Página1
                            n_cliente_value = get_value(row, "Nº CLIENTE", "")
                            maquinas_cliente["Nº CLIENTE"] = n_cliente_value
                            
                            # Reordenar colunas: N°, Nº CLIENTE, depois as demais
                            cols_ordenadas = ["N°", "Nº CLIENTE"] + [col for col in maquinas_cliente.columns if col not in ["N°", "Nº CLIENTE", "CLIENTES"]]
                            maquinas_cliente = maquinas_cliente[cols_ordenadas]

                            # Ajuste dos cabeçalhos (Primeira letra maiúscula)
                            maquinas_cliente.columns = [col.capitalize() for col in maquinas_cliente.columns]

                            # Centralizar dados
                            st.markdown(
                                """
                                <style>
                                table td, table th {
                                    text-align: center !important;
                                }
                                </style>
                                """,
                                unsafe_allow_html=True
                            )

                            st.dataframe(maquinas_cliente.reset_index(drop=True))
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
                    cliente = st.text_input("CLIENTE*")
                    consultor = st.text_input("CONSULTOR*")
                    revenda = st.text_input("REVENDA*")
                
                with col2:
                    pssr = st.text_input("PSSR*")
                    cnpj_cpf = st.text_input("CNPJ/CPF*")
                    contato = st.text_input("CONTATO*")
                    n_cliente = st.text_input("Nº CLIENTE*")
                
                submitted = st.form_submit_button("Cadastrar Cliente")
                
                if submitted:
                    if not all([cliente, consultor, revenda, pssr, cnpj_cpf, contato, n_cliente]):
                        st.error("Todos os campos marcados com * são obrigatórios!")
                    else:
                        try:
                            # Preparar dados
                            novo_cliente = {
                                "CLIENTES": cliente,
                                "NOVO CONSULTOR": consultor,
                                "REVENDA": revenda,
                                "PSSR": pssr,
                                "CNPJ/CPF": cnpj_cpf,
                                "CONTATO": contato,
                                "Nº CLIENTE": n_cliente
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
                
                # Selecionar cliente para ajuste
                opcoes_clientes = sorted(df_pagina1["CLIENTES"].dropna().unique())
                cliente_ajuste = st.selectbox("Selecione o cliente para ajuste:", opcoes_clientes)
                
                if cliente_ajuste:
                    # Obter dados do cliente selecionado
                    cliente_data = df_pagina1[df_pagina1["CLIENTES"] == cliente_ajuste].iloc[0]
                    
                    with st.form("form_ajuste"):
                        st.subheader(f"Editando: {cliente_ajuste}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            novo_cliente = st.text_input("CLIENTE", value=get_value(cliente_data, "CLIENTES"))
                            novo_consultor = st.text_input("CONSULTOR", value=get_value(cliente_data, "NOVO CONSULTOR"))
                            nova_revenda = st.text_input("REVENDA", value=get_value(cliente_data, "REVENDA"))
                        
                        with col2:
                            novo_pssr = st.text_input("PSSR", value=get_value(cliente_data, "PSSR"))
                            novo_cnpj = st.text_input("CNPJ/CPF", value=get_value(cliente_data, "CNPJ/CPF"))
                            novo_contato = st.text_input("CONTATO", value=get_value(cliente_data, "CONTATO"))
                            novo_n_cliente = st.text_input("Nº CLIENTE", value=get_value(cliente_data, "Nº CLIENTE"))
                        
                        submitted = st.form_submit_button("Salvar Alterações")
                        
                        if submitted:
                            try:
                                # Encontrar índice da linha
                                row_index = df_pagina1[df_pagina1["CLIENTES"] == cliente_ajuste].index[0] + 2  # +2 porque a planilha tem cabeçalho e índice começa em 1
                                
                                # Preparar dados para atualização
                                dados_atualizados = {
                                    "CLIENTES": novo_cliente,
                                    "NOVO CONSULTOR": novo_consultor,
                                    "REVENDA": nova_revenda,
                                    "PSSR": novo_pssr,
                                    "CNPJ/CPF": novo_cnpj,
                                    "CONTATO": novo_contato,
                                    "Nº CLIENTE": novo_n_cliente
                                }
                                
                                # Atualizar na planilha
                                if update_sheet_data(client, SPREADSHEET_URL, "Página1", row_index, dados_atualizados):
                                    st.success("Dados atualizados com sucesso!")
                                    st.cache_data.clear()
                                else:
                                    st.error("Erro ao atualizar dados.")
                                    
                            except Exception as e:
                                st.error(f"Erro ao atualizar: {e}")
                
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
        Versão 1.4.1 • Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
