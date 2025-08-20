import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import os

# ——————————————————————————————
# CONFIGURAÇÃO DA PÁGINA
# ——————————————————————————————
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# ——————————————————————————————
# FUNÇÃO DE CREDENCIAIS
# ——————————————————————————————
def get_google_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Verificar se há arquivo JSON de credenciais na pasta
    if os.path.exists("credenciais.json"):
        try:
            return Credentials.from_service_account_file("credenciais.json", scopes=scopes)
        except Exception as e:
            st.error(f"Erro ao carregar credenciais.json: {e}")
    
    # Tentar usar secrets do Streamlit
    try:
        if "gcp_service_account" in st.secrets:
            service_account_info = dict(st.secrets["gcp_service_account"])
            return Credentials.from_service_account_info(service_account_info, scopes=scopes)
    except Exception as e:
        st.error(f"Erro nas credenciais do secrets: {e}")
    
    return None

# ——————————————————————————————
# FUNÇÃO PARA CARREGAR PLANILHA
# ——————————————————————————————
def load_sheet_data(client, spreadsheet_url):
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        available_sheets = [ws.title for ws in spreadsheet.worksheets()]
        sheet_name = "Página1"
        if sheet_name not in available_sheets:
            raise Exception(f"Aba '{sheet_name}' não encontrada. Abas disponíveis: {', '.join(available_sheets)}")
        worksheet = spreadsheet.worksheet(sheet_name)
        records = worksheet.get_all_records()
        if not records:
            raise Exception("A planilha está vazia ou não contém dados formatados como uma tabela.")
        df = pd.DataFrame(records).dropna(how="all")
        df.columns = [c.strip().upper() for c in df.columns]
        required_cols = {'CLIENTES', 'NOVO CONSULTOR', 'REVENDA'}
        missing = required_cols - set(df.columns)
        if missing:
            raise Exception(f"Colunas obrigatórias faltando: {', '.join(missing)}")
        return df
    except Exception as e:
        st.error(f"📊 Erro ao carregar dados da planilha: {e}")
        return None

# ——————————————————————————————
# INTERFACE PRINCIPAL
# ——————————————————————————————
def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")
    
    # Obter credenciais
    creds = get_google_creds()
    
    if creds is None:
        st.warning("🔐 Credenciais não encontradas")
        
        # Seção de upload mais destacada
        st.markdown("---")
        st.subheader("📤 Upload do Arquivo de Credenciais")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("""
            **Como obter o arquivo de credenciais:**
            1. Acesse o Google Cloud Console
            2. Crie uma Service Account
            3. Faça download do arquivo JSON
            4. Faça upload abaixo
            """)
            
            uploaded_file = st.file_uploader(
                "Selecione o arquivo JSON de credenciais",
                type="json",
                help="Arquivo JSON da Service Account do Google Cloud"
            )
            
            if uploaded_file is not None:
                try:
                    # Ler o conteúdo do arquivo
                    credentials_json = json.load(uploaded_file)
                    creds = Credentials.from_service_account_info(credentials_json, scopes=[
                        "https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"
                    ])
                    
                    # Salvar o arquivo localmente para uso futuro
                    with open("credenciais.json", "w") as f:
                        json.dump(credentials_json, f)
                    
                    st.success("✅ Credenciais carregadas com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {e}")
        
        with col2:
            st.markdown("""
            **📋 Formato Esperado:**
            ```json
            {
              "type": "service_account",
              "project_id": "...",
              "private_key_id": "...",
              "private_key": "-----BEGIN PRIVATE KEY-----...",
              "client_email": "...",
              "client_id": "...",
              "auth_uri": "...",
              "token_uri": "...",
              "auth_provider_x509_cert_url": "...",
              "client_x509_cert_url": "..."
            }
            ```
            """)
        
        st.markdown("---")
        return

    # Se as credenciais foram obtidas com sucesso, continuar
    try:
        client = gspread.authorize(creds)
        st.success("🔓 Conectado ao Google Sheets com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Google Sheets: {e}")
        return

    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1sresryYLTR8aCp2ZCR82kfQKaUrqLxeFBVpVI2Yw7_I/edit?usp=sharing"

    @st.cache_data(ttl=3600)
    def get_data():
        return load_sheet_data(client, SPREADSHEET_URL)

    with st.spinner("📊 Carregando dados da planilha..."):
        df = get_data()
        if df is None or df.empty:
            st.warning("⚠️ Nenhum dado disponível para exibir.")
            return

    # Mensagem de sucesso
    total_registros = f"{len(df):,}".replace(",", ".")
    st.success(f"✅ {total_registros} registros carregados!")

    # Busca de cliente
    st.subheader("🔎 Buscar Cliente")
    cliente = st.selectbox(
        "Selecione um cliente:",
        sorted(df["CLIENTES"].dropna().unique())
    )

    # Exibir dados do cliente
    if cliente:
        row = df[df["CLIENTES"] == cliente].iloc[0]
        st.markdown(
            f"""
            <div style='
                background-color: #1e1e1e;
                border-radius: 10px;
                padding: 15px;
                margin-top: 15px;
                display: inline-block;
                box-shadow: 0px 2px 6px rgba(0,0,0,0.4);
            '>
                <p style='font-size:20px; margin: 5px 0;'>
                    <strong style='color:#4CAF50;'>👤 Consultor:</strong>
                    <span style='font-weight:bold; color:white;'>{row['NOVO CONSULTOR']}</span>
                </p>
                <p style='font-size:20px; margin: 5px 0;'>
                    <strong style='color:#2196F3;'>🏢 Revenda:</strong>
                    <span style='font-weight:bold; color:white;'>{row['REVENDA']}</span>
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Rodapé
    st.markdown("---")
    st.markdown(
        f"""
        <p style='text-align: center; font-size: 12px; color: gray;'>
            © {datetime.now().year} NORMAQ JCB - Todos os direitos reservados<br>
            Versão: 1.2.0 | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
