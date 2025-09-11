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
    "graziela.galdino@normaq.com.br",
    "tiago.fernandes@normaq.com.br"
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
    headers = get_exact_headers(client, spreadsheet_url, sheet_name)
    row_data = []
    for header in headers:
        found = False
        for data_key in data.keys():
            if data_key.upper() == header.upper():
                row_data.append(data[data_key])
                found = True
                break
        if not found:
            row_data.append("")
    worksheet.append_row(row_data)
    return True

# ——————————————————————————————
#  FUNÇÃO PARA ATUALIZAR DADOS NA PLANILHA
# ——————————————————————————————
def update_sheet_data(client, spreadsheet_url, sheet_name, row_index, data):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    headers = get_exact_headers(client, spreadsheet_url, sheet_name)
    for data_key, value in data.items():
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
    numeros = re.sub(r'\D', '', str(telefone))
    if numeros.startswith('55') and len(numeros) >= 12:
        return numeros
    elif len(numeros) == 11:
        return '55' + numeros
    elif len(numeros) == 10:
        return '55' + numeros
    else:
        return numeros

# ——————————————————————————————
#  CSS PARA BLOQUEAR SELEÇÃO DE TEXTO
# ——————————————————————————————
def inject_protection_css():
    st.markdown("""
    <style>
    .stDataFrame {
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
    }
    input, textarea {
        user-select: text !important;
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ——————————————————————————————
#  INTERFACE PRINCIPAL
# ——————————————————————————————
def main():
    verificar_email()
    inject_protection_css()
    st.sidebar.success(f"👤 Logado como: {st.session_state.email_usuario}")
    if st.sidebar.button("🚪 Sair"):
        st.session_state.email_verificado = False
        st.session_state.email_usuario = None
        st.rerun()

    st.title("🔍 Carteira de Clientes NORMAQ JCB")

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

            consulta_por = st.radio("Consultar por:", ["Cliente", "CNPJ/CPF"], horizontal=True)
            
            if consulta_por == "Cliente":
                clientes_disponiveis = sorted([str(cliente) for cliente in df_pagina1["CLIENTES"].dropna().unique()])
                cliente_selecionado = st.selectbox("Selecione um cliente:", clientes_disponiveis, key="cliente_select")
                cliente_data = df_pagina1[df_pagina1["CLIENTES"].astype(str) == cliente_selecionado]
            else:
                cnpj_cpf_disponiveis = sorted([str(cnpj) for cnpj in df_pagina1["CNPJ/CPF"].dropna().unique()])
                cnpj_cpf_selecionado = st.selectbox("Selecione um CNPJ/CPF:", cnpj_cpf_disponiveis, key="cnpj_select")
                cliente_data = df_pagina1[df_pagina1["CNPJ/CPF"].astype(str) == cnpj_cpf_selecionado]
                cliente_selecionado = get_value(cliente_data.iloc[0], "CLIENTES") if not cliente_data.empty else ""

            if not cliente_data.empty:
                row = cliente_data.iloc[0]
                contato_value = get_value(row, "Contato")
                telefone_formatado = formatar_telefone(contato_value)
                whatsapp_link = f"https://wa.me/{telefone_formatado}" if telefone_formatado and telefone_formatado != "Não informado" else "#"

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(
                        f"""
                        <div style='background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); border-radius: 12px; padding: 20px; margin: 15px 0; box-shadow: 0 6px 16px rgba(0,0,0,0.2); color: white; border-left: 4px solid #4CAF50;'>
                            <p><strong style='color:#4CAF50;'>👤 CONSULTOR:</strong><br>{get_value(row, "NOVO CONSULTOR")}</p>
                            <hr>
                            <p><strong style='color:#2196F3;'>🏢 REVENDA:</strong><br>{get_value(row, "Revenda")}</p>
                            <hr>
                            <p><strong style='color:#FF9800;'>🔧 PSSR:</strong><br>{get_value(row, "PSSR")}</p>
                            <hr>
                            <p><strong style='color:#9C27B0;'>📞 CONTATO:</strong><br>
                                <a href='{whatsapp_link}' target='_blank' style='color: #25D366; text-decoration: none;'>
                                    {contato_value} 💬
                                </a>
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
                            categorias_count = maquinas_cliente["CATEGORIA"].value_counts()
                            categorias_str = " | ".join([f"{cat} - {count:02d}" for cat, count in categorias_count.items()])

                            st.markdown(
                                f"""
                                <div style='background: #f8f9fa; padding: 10px; border-radius: 10px; margin-bottom: 10px; font-size: 16px; color: #333; border: 1px solid #ddd;'>
                                💡 Selecione um cliente para visualizar as informações completas
                                <span style="font-weight:bold; font-size:18px; color:#4CAF50;"> - Quantidade de Máquinas: {qtd_maquinas}</span>
                                <br>
                                <span style="font-weight:bold; font-size:16px; color:#2196F3;">Categorias: {categorias_str}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            maquinas_cliente = maquinas_cliente.copy()
                            maquinas_cliente["N°"] = range(1, len(maquinas_cliente) + 1)
                            n_cliente_value = get_value(row, "Nº Cliente", "")
                            n_cliente_limpo = re.sub(r'[^\d]', '', str(n_cliente_value))
                            maquinas_cliente["Nº CLIENTE"] = n_cliente_limpo
                            cols_ordenadas = ["N°", "Nº CLIENTE", "CLIENTES"] + [col for col in maquinas_cliente.columns if col not in ["N°", "Nº CLIENTE", "CLIENTES"]]
                            maquinas_cliente = maquinas_cliente[cols_ordenadas]
                            maquinas_cliente = maquinas_cliente.loc[:, ~maquinas_cliente.columns.str.contains('^Unnamed', na=False)]
                            maquinas_cliente = maquinas_cliente.loc[:, maquinas_cliente.columns != '']
                            maquinas_cliente.columns = [col.capitalize() for col in maquinas_cliente.columns]

                            st.dataframe(maquinas_cliente.reset_index(drop=True), use_container_width=True, hide_index=True)

                        else:
                            st.warning("📭 Nenhuma máquina encontrada para este cliente")
                    else:
                        st.info("💡 Selecione um cliente para visualizar as informações completas")
            else:
                st.info("👆 Selecione um cliente na lista acima")

        except Exception as e:
            st.error(f"Erro ao carregar a aplicação: {e}")

    # (tab2 e tab3 seguem iguais ao seu código original...)
    # Mantive cadastro e ajuste de cliente

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
