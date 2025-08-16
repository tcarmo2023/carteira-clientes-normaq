import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ——————————————————————————————
#  CONFIGURAÇÃO DA PÁGINA
# ——————————————————————————————
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# ——————————————————————————————
#  FUNÇÃO DE CREDENCIAIS
# ——————————————————————————————
def get_google_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        if "gcp_service_account" in st.secrets:
            return Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=scopes
            )
        # Lugar alternativo — arquivos locais (não usado no Cloud)
        st.error("Erro nas credenciais: gcp_service_account não encontrado")
        st.stop()
    except Exception as e:
        st.error(f"🔐 Erro nas credenciais: {e}")
        st.stop()

# ——————————————————————————————
#  FUNÇÃO PARA CARREGAR PLANILHA
# ——————————————————————————————
def load_sheet_data(client, spreadsheet_url):
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        available_sheets = [ws.title for ws in spreadsheet.worksheets()]
        
        sheet_name = "Página1"  # Ajustado para o nome correto da aba
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
#  INTERFACE PRINCIPAL
# ——————————————————————————————
def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")
    
    creds = get_google_creds()
    client = gspread.authorize(creds)
    
    # URL da planilha no formato compartilhável
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1sresryYLTR8aCp2ZCR82kfQKaUrqLxeFBVpVI2Yw7_I/edit?usp=sharing"
    
    @st.cache_data(ttl=3600)
    def get_data():
        return load_sheet_data(client, SPREADSHEET_URL)
    
    with st.spinner("Carregando dados da planilha..."):
        df = get_data()
    
    if df is None or df.empty:
        st.warning("⚠️ Nenhum dado disponível para exibir.")
        return
    
    st.success(f"✅ {len(df)} registros carregados!")
    
    # ——————————————————————————————
    # Pesquisa interativa
    st.subheader("🔎 Buscar Cliente")
    cliente = st.selectbox(
        "Selecione um cliente:",
        sorted(df["CLIENTES"].dropna().unique())
    )
    
    if cliente:
        row = df[df["CLIENTES"] == cliente].iloc[0]
        st.write(f"**👤 Consultor:** {row['NOVO CONSULTOR']}")
        st.write(f"**🏢 Revenda:** {row['REVENDA']}")

if __name__ == "__main__":
    main()
