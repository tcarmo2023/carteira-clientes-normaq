import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# ——————————————————————————————
#  CONFIGURAÇÃO DA PÁGINA
# ——————————————————————————————
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# ——————————————————————————————
#  FUNÇÃO DE CREDENCIAIS - CORRIGIDA
# ——————————————————————————————
def get_google_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # Verifica se existe no secrets do Streamlit
        if hasattr(st.secrets, "gcp_service_account"):
            creds_data = st.secrets.gcp_service_account
            
            # Se for dict (formato TOML), usa diretamente
            if isinstance(creds_data, dict):
                return Credentials.from_service_account_info(creds_data, scopes=scopes)
            
            # Se for string (formato JSON), converte
            elif isinstance(creds_data, str):
                try:
                    creds_dict = json.loads(creds_data)
                    return Credentials.from_service_account_info(creds_dict, scopes=scopes)
                except json.JSONDecodeError as e:
                    st.error(f"❌ JSON inválido: {e}")
                    st.error("Verifique a formatação do JSON")
                    st.stop()
        
        # Fallback para arquivo local
        try:
            return Credentials.from_service_account_file("credentials.json", scopes=scopes)
        except FileNotFoundError:
            st.error("""
            ❌ Nenhuma credencial encontrada!
            
            Configure o secrets.toml no Streamlit Cloud com:
            
            **Formato TOML (RECOMENDADO):**
            ```toml
            [gcp_service_account]
            type = "service_account"
            project_id = "seu-project-id"
            private_key_id = "sua-private-key-id"
            private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
            client_email = "seu-email@projeto.iam.gserviceaccount.com"
            client_id = "123456789"
            auth_uri = "https://accounts.google.com/o/oauth2/auth"
            token_uri = "https://oauth2.googleapis.com/token"
            auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
            client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
            universe_domain = "googleapis.com"
            ```
            """)
            st.stop()
            
    except Exception as e:
        st.error(f"🔐 Erro nas credenciais: {str(e)}")
        st.error("Verifique se a chave privada está completa e bem formatada")
        st.stop()

# ——————————————————————————————
#  RESTANTE DO CÓDIGO (MANTIDO)
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

def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")
    
    try:
        with st.spinner("Conectando ao Google Sheets..."):
            creds = get_google_creds()
            client = gspread.authorize(creds)
        st.success("✅ Autenticação bem-sucedida!")
        
        SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1sresryYLTR8aCp2ZCR82kfQKaUrqLxeFBVpVI2Yw7_I/edit?usp=sharing"
        
        @st.cache_data(ttl=3600)
        def get_data():
            return load_sheet_data(client, SPREADSHEET_URL)
        
        with st.spinner("Carregando dados da planilha..."):
            df = get_data()
        
        if df is None or df.empty:
            st.warning("⚠️ Nenhum dado disponível para exibir.")
            return
        
        total_registros = f"{len(df):,}".replace(",", ".")
        st.success(f"✅ {total_registros} registros carregados!")
        
        st.subheader("🔎 Buscar Cliente")
        cliente = st.selectbox(
            "Selecione um cliente:",
            sorted(df["CLIENTES"].dropna().unique())
        )
        
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
        
    except Exception as e:
        st.error(f"⛔ Erro na aplicação: {str(e)}")
    
    st.markdown(
        f"""
        <hr>
        <p style='text-align: center; font-size: 12px; color: gray;'>
        © {datetime.now().year} NORMAQ JCB - Todos os direitos reservados<br>
        Versão: 1.1.0 | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
