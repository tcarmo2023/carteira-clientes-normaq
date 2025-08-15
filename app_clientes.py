import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sys

def main():
    # Configuração da página
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
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔍 Carteira de Clientes NORMAQ JCB")

    # Carregar dados
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("Carteira de Clientes_v02.xlsx").sheet1
        dados = sheet.get_all_records()
        df = pd.DataFrame(dados).dropna(how='all')
        
        # Verificar colunas necessárias
        required_cols = ['CLIENTES', 'NOVO CONSULTOR', 'REVENDA']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Planilha não contém todas as colunas necessárias: {required_cols}")
            st.stop()
            
        # Interface de busca
        opcao_busca = st.radio("Buscar por:", ("Cliente", "Consultor", "Revenda"), horizontal=True)
        
        if opcao_busca == "Cliente":
            cliente = st.selectbox("Selecione o cliente:", sorted(df["CLIENTES"].astype(str).unique()))
            resultado = df[df["CLIENTES"].astype(str) == cliente]
        elif opcao_busca == "Consultor":
            consultor = st.selectbox("Selecione o consultor:", sorted(df["NOVO CONSULTOR"].astype(str).unique()))
            resultado = df[df["NOVO CONSULTOR"].astype(str) == consultor]
        else:
            revenda = st.selectbox("Selecione a revenda:", sorted(df["REVENDA"].astype(str).unique()))
            resultado = df[df["REVENDA"].astype(str) == revenda]

        if st.button("Buscar"):
            if not resultado.empty:
                st.markdown("### Resultado da Busca")
                for _, row in resultado.iterrows():
                    st.markdown(f"""
                    <div class="client-card">
                        <p><strong>Cliente:</strong> {row['CLIENTES']}</p>
                        <p><strong>Consultor:</strong> {row['NOVO CONSULTOR']}</p>
                        <p><strong>Revenda:</strong> {row['REVENDA']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Nenhum resultado encontrado.")
                
    except FileNotFoundError:
        st.error("Arquivo credentials.json não encontrado!")
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Planilha não encontrada. Verifique o nome!")
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")

    st.markdown("---")
    st.markdown("© 2024 NORMAQ JCB - Todos os direitos reservados")

if __name__ == "__main__":
    main()