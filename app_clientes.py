import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# [Seu CSS personalizado permanece igual...]

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
                
        raise FileNotFoundError("Nenhum arquivo de credenciais encontrado")
        
    except Exception as e:
        st.error(f"🔐 Erro nas credenciais: {str(e)}")
        st.stop()

def load_sheet_data(client, spreadsheet_name):
    """Carrega dados com tratamento robusto de erros"""
    try:
        # Verifica se a planilha existe
        try:
            spreadsheet = client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            raise Exception(f"Planilha '{spreadsheet_name}' não encontrada")
        
        # Verifica se a aba existe
        try:
            worksheet = spreadsheet.worksheet("Carteira")
        except gspread.WorksheetNotFound:
            available_sheets = [ws.title for ws in spreadsheet.worksheets()]
            raise Exception(f"Aba 'Carteira' não encontrada. Abas disponíveis: {', '.join(available_sheets)}")
        
        # Obtém os dados
        records = worksheet.get_all_records()
        
        if not records:
            raise Exception("A planilha está vazia ou não contém dados formatados como tabela")
            
        df = pd.DataFrame(records).dropna(how='all')
        
        # Verifica colunas obrigatórias
        required_cols = {'CLIENTES', 'NOVO CONSULTOR', 'REVENDA'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise Exception(f"Colunas obrigatórias faltando: {', '.join(missing_cols)}")
            
        return df
        
    except Exception as e:
        st.error(f"📊 Erro ao carregar dados: {str(e)}")
        st.stop()

def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")
    
    try:
        # Autenticação com feedback
        with st.spinner("Conectando ao Google Sheets..."):
            try:
                creds = get_google_creds()
                client = gspread.authorize(creds)
                st.success("✅ Autenticação bem-sucedida!")
            except Exception as e:
                st.error(f"🔐 Falha na autenticação: {str(e)}")
                st.stop()
        
        # Carregamento de dados
        @st.cache_data(ttl=3600)
        def get_data():
            return load_sheet_data(client, "Carreira de Clientes_v02.xlsx")
            
        with st.spinner("Carregando dados da planilha..."):
            try:
                df = get_data()
                st.success(f"✅ Dados carregados! {len(df)} registros encontrados")
            except Exception as e:
                st.error(f"📊 Falha ao carregar dados: {str(e)}")
                st.stop()
        
        # [Restante do seu código de interface permanece igual...]
        
    except Exception as e:
        st.error(f"⛔ Erro crítico: {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()
