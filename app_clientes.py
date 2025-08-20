import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import sys

# ---------------- CONFIGURAÇÃO DA PÁGINA ---------------- #
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# ---------------- VERIFICAÇÃO DE EXECUÇÃO ---------------- #
def is_running_with_streamlit():
    """Verifica se o script está sendo executado com streamlit run"""
    return 'streamlit' in sys.modules

# ---------------- FUNÇÃO DE CREDENCIAIS ---------------- #
def get_google_creds():
    """Obtém credenciais do Google Sheets com tratamento de erros aprimorado"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # 1. Tentar secrets.toml (Streamlit Cloud)
        if 'gcp_service_account' in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )
            return creds
        
        # 2. Tentar credentials.json (local)
        creds_paths = [
            "credentials.json",
            os.path.join(os.path.expanduser("~"), "credentials.json"),
            "/workspaces/carteira-clientes-normaq/credentials.json"
        ]
        
        for path in creds_paths:
            if os.path.exists(path):
                creds = Credentials.from_service_account_file(path, scopes=scopes)
                return creds
                
        # 3. Interface para upload de credenciais
        st.sidebar.warning("🔐 Credenciais não encontradas")
        uploaded_file = st.sidebar.file_uploader(
            "Faça upload do arquivo credentials.json", 
            type="json"
        )
        
        if uploaded_file is not None:
            # Salvar o arquivo temporariamente
            with open("temp_credentials.json", "wb") as f:
                f.write(uploaded_file.getvalue())
            creds = Credentials.from_service_account_file("temp_credentials.json", scopes=scopes)
            os.remove("temp_credentials.json")  # Limpar após uso
            return creds
        else:
            st.error("""
            ❌ Não foi possível encontrar as credenciais do Google Sheets.
            
            Para usar esta aplicação, você precisa:
            1. Criar uma Service Account no Google Cloud Console
            2. Fazer o download do arquivo credentials.json
            3. Fazer o upload do arquivo usando o menu à esquerda
            """)
            st.stop()
            
    except Exception as e:
        st.error(f"🔐 Erro nas credenciais: {str(e)}")
        st.stop()

# ---------------- FUNÇÃO PARA CARREGAR PLANILHA ---------------- #
def load_sheet_data(client, spreadsheet_name, worksheet_name="Página1"):
    """Carrega dados com tratamento robusto de erros"""
    try:
        # Verifica se a planilha existe
        try:
            spreadsheet = client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            st.error(f"Planilha '{spreadsheet_name}' não encontrada")
            st.info("Verifique se o nome da planilha está correto e se a conta de serviço tem acesso a ela")
            return None

        # Verifica se a aba existe
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            available_sheets = [ws.title for ws in spreadsheet.worksheets()]
            st.error(f"Aba '{worksheet_name}' não encontrada.")
            st.info(f"Abas disponíveis: {', '.join(available_sheets)}")
            return None
        
        # Obtém os dados
        records = worksheet.get_all_records()
        
        if not records:
            st.warning("A planilha está vazia ou não contém dados formatados como tabela")
            return pd.DataFrame()
            
        df = pd.DataFrame(records).dropna(how='all')
        
        if df.empty:
            st.warning("Nenhum dado válido encontrado após remover linhas vazias")
            return pd.DataFrame()
            
        # Verifica colunas obrigatórias
        required_cols = {'CLIENTES', 'NOVO CONSULTOR', 'REVENDA'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            st.error(f"Colunas obrigatórias faltando: {', '.join(missing_cols)}")
            st.info(f"Colunas encontradas: {', '.join(df.columns)}")
            return None
            
        return df
        
    except Exception as e:
        st.error(f"📊 Erro ao carregar dados: {str(e)}")
        return None

# ---------------- INTERFACE PRINCIPAL ---------------- #
def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")
    st.markdown("---")
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Informações")
        st.markdown("""
        Esta aplicação permite visualizar e buscar 
        informações da carteira de clientes da NORMAQ JCB.
        """)
        
        st.header("⚙️ Configuração")
        spreadsheet_name = st.text_input(
            "Nome da planilha", 
            value="Carteira de Clientes_v02"
        )
        worksheet_name = st.text_input(
            "Nome da aba", 
            value="Página1"
        )
    
    try:
        # Autenticação com feedback
        with st.spinner("Conectando ao Google Sheets..."):
            creds = get_google_creds()
            client = gspread.authorize(creds)
            st.success("✅ Autenticação bem-sucedida!")
        
        # Carregamento de dados
        @st.cache_data(ttl=3600, show_spinner="Carregando dados da planilha...")
        def get_data():
            return load_sheet_data(client, spreadsheet_name, worksheet_name)
        
        df = get_data()
        
        if df is None:
            st.error("Falha ao carregar os dados. Verifique as configurações.")
            st.stop()
            
        if df.empty:
            st.warning("⚠️ Nenhum dado foi carregado. Verifique a planilha.")
            st.stop()
            
        st.success(f"✅ {len(df)} registros carregados!")
        
        # Exibir visualização rápida dos dados
        with st.expander("📋 Visualizar todos os dados"):
            st.dataframe(df, use_container_width=True)
        
        # ---------------- BUSCA POR CLIENTE ---------------- #
        st.subheader("🔎 Buscar Cliente")
        
        # Adicionar busca por texto
        search_term = st.text_input("Digite para filtrar clientes:", "")
        
        # Filtrar opções com base no termo de busca
        client_options = sorted(df["CLIENTES"].unique())
        if search_term:
            client_options = [client for client in client_options if search_term.lower() in client.lower()]
        
        if not client_options:
            st.warning("Nenhum cliente encontrado com o termo de busca.")
        else:
            cliente_escolhido = st.selectbox(
                "Selecione um cliente:",
                options=client_options
            )
            
            if cliente_escolhido:
                resultado = df[df["CLIENTES"] == cliente_escolhido].iloc[0]
                
                st.markdown("---")
                st.subheader(f"📋 Informações do Cliente: {cliente_escolhido}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**👤 Consultor:** {resultado['NOVO CONSULTOR']}")
                with col2:
                    st.info(f"**🏢 Revenda:** {resultado['REVENDA']}")
                
                # Exibir todas as informações disponíveis
                st.markdown("**📊 Todas as informações disponíveis:**")
                info_df = pd.DataFrame({
                    'Campo': resultado.index,
                    'Valor': resultado.values
                })
                st.dataframe(info_df, hide_index=True, use_container_width=True)
    
    except Exception as e:
        st.error(f"⛔ Erro crítico: {str(e)}")
        st.stop()

if __name__ == "__main__":
    if is_running_with_streamlit():
        main()
    else:
        st.error("""
        ❌ Este aplicativo deve ser executado com o comando:
        
        `streamlit run app_clientes.py`
        
        Execute no terminal:
        ```
        streamlit run /workspaces/carteira-clientes-normaq/app_clientes.py
        ```
        """)
