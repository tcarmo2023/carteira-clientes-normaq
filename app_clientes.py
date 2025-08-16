import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

# Configuração da página (fora da função main para evitar reexecução)
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# CSS personalizado
st.markdown("""
<style>
.stApp { background-color: #FCAF26; }
.client-card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    margin: 10px 0;
}
.search-header {
    color: #2c3e50;
    margin-bottom: 15px;
}
.footer {
    margin-top: 30px;
    text-align: center;
    color: #7f8c8d;
}
.stButton>button {
    background-color: #2c3e50;
    color: white;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #1a2b3c;
    color: white;
}
</style>
""", unsafe_allow_html=True)

def get_google_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    if 'gcp_service_account' not in st.secrets:
        st.error("Credenciais não encontradas no secrets.toml")
        st.stop()
        
    try:
        return Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
    except Exception as e:
        st.error(f"Erro ao carregar credenciais: {str(e)}")
        st.stop()
    
    # 2. Tentar locais alternativos para credentials.json
    creds_paths = [
        "credentials.json",
        os.path.join(os.path.dirname(__file__), "credentials.json"),
        "/workspaces/carteira-clientes-normaq/credentials.json",
        os.path.expanduser("~/credentials.json")
    ]
    
    for path in creds_paths:
        if os.path.exists(path):
            try:
                return Credentials.from_service_account_file(path, scopes=scopes)
            except Exception as e:
                st.error(f"Erro ao ler credenciais em {path}")
                st.error(str(e))
                continue
    
    st.error("""
    🔐 Credenciais não encontradas!
    - Para desenvolvimento local: coloque credentials.json na pasta do projeto
    - Para produção: configure secrets.toml
    """)
    st.stop()

def load_sheet_data(client, spreadsheet_name):
    """Carrega dados da planilha com tratamento de erros"""
    try:
        sheet = client.open(spreadsheet_name).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data).dropna(how='all')
        
        # Converter colunas de texto para string
        text_cols = ['CLIENTES', 'NOVO CONSULTOR', 'REVENDA']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                
        return df
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"📂 Planilha '{spreadsheet_name}' não encontrada!")
        st.error("Verifique o nome no Google Sheets")
        st.stop()
    except Exception as e:
        st.error(f"⛔ Erro ao carregar dados: {str(e)}")
        st.stop()

def display_client_card(row):
    """Exibe o cartão de informações do cliente"""
    with st.container():
        st.markdown(f"""
        <div class="client-card">
            <p><strong>👤 Cliente:</strong> {row['CLIENTES']}</p>
            <p><strong>🛠 Consultor:</strong> {row['NOVO CONSULTOR']}</p>
            <p><strong>🏢 Revenda:</strong> {row['REVENDA']}</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")
    
    try:
        # Autenticação
        with st.spinner("Conectando ao Google Sheets..."):
            creds = get_google_credentials()
            client = gspread.authorize(creds)
        
        # Carregar dados (com cache de 1 hora)
        @st.cache_data(ttl=3600, show_spinner="Carregando dados da planilha...")
        def get_data():
            return load_sheet_data(client, "Carteira de Clientes_v02.xlsx")
            
        df = get_data()
        
        # Validação das colunas
        required_cols = ['CLIENTES', 'NOVO CONSULTOR', 'REVENDA']
        if not all(col in df.columns for col in required_cols):
            st.error(f"⚠️ A planilha está faltando colunas necessárias: {', '.join(required_cols)}")
            st.stop()
        
        # Interface de busca
        st.markdown("### 🔎 Busca", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        
        with col1:
            search_type = st.radio(
                "Buscar por:",
                ("Cliente", "Consultor", "Revenda"),
                horizontal=True,
                key="search_type"
            )
            
            # Filtros de busca
            if search_type == "Cliente":
                filter_value = st.selectbox(
                    "Selecione o cliente:",
                    sorted(df["CLIENTES"].unique()),
                    key="client_select"
                )
                results = df[df["CLIENTES"] == filter_value]
            elif search_type == "Consultor":
                filter_value = st.selectbox(
                    "Selecione o consultor:",
                    sorted(df["NOVO CONSULTOR"].unique()),
                    key="consultant_select"
                )
                results = df[df["NOVO CONSULTOR"] == filter_value]
            else:
                filter_value = st.selectbox(
                    "Selecione a revenda:",
                    sorted(df["REVENDA"].unique()),
                    key="reseller_select"
                )
                results = df[df["REVENDA"] == filter_value]
        
        if st.button("Buscar", type="primary", use_container_width=True):
            if not results.empty:
                st.markdown(f"### 📋 Resultados ({len(results)} encontrados)")
                for _, row in results.iterrows():
                    display_client_card(row)
            else:
                st.warning("Nenhum resultado encontrado para esta busca.")
                
    except Exception as e:
        st.error(f"⛔ Ocorreu um erro inesperado: {str(e)}")
        st.error("Consulte o console para detalhes técnicos")

    # Rodapé
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
        © {datetime.now().year} NORMAQ JCB - Todos os direitos reservados<br>
        Versão: 1.1.0 | Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
