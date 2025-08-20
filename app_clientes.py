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
#  FUNÇÃO DE CREDENCIAIS - SEM MENSAGENS
# ——————————————————————————————
def get_google_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        if not hasattr(st.secrets, "gcp_service_account"):
            st.error("Credenciais não configuradas")
            st.stop()
            
        creds_config = st.secrets.gcp_service_account
        
        # Verificação silenciosa dos campos obrigatórios
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_config]
        
        if missing_fields:
            st.error("Configuração incompleta das credenciais")
            st.stop()
            
        # Verifica chave privada silenciosamente
        private_key = creds_config['private_key']
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----') or not private_key.endswith('-----END PRIVATE KEY-----'):
            st.error("Formato inválido da chave privada")
            st.stop()
        
        return Credentials.from_service_account_info(creds_config, scopes=scopes)
        
    except Exception:
        st.error("Erro ao carregar credenciais")
        st.stop()

# ——————————————————————————————
#  FUNÇÃO PARA CARREGAR PLANILHA - SEM MENSAGENS
# ——————————————————————————————
def load_sheet_data(client, spreadsheet_url):
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        
        # Tenta encontrar a aba correta silenciosamente
        sheet_names = ["Página1", "Carteira", "Sheet1", "Planilha1"]
        worksheet = None
        
        for sheet_name in sheet_names:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                break
            except:
                continue
                
        if worksheet is None:
            return None
        
        records = worksheet.get_all_records()
        if not records:
            return None
        
        df = pd.DataFrame(records).dropna(how="all")
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        return df
        
    except Exception:
        return None

# ——————————————————————————————
#  INTERFACE PRINCIPAL LIMPA
# ——————————————————————————————
def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")
    
    # Container principal para evitar flickering
    main_container = st.container()
    
    with main_container:
        try:
            # Autenticação silenciosa
            creds = get_google_creds()
            client = gspread.authorize(creds)
            
            SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1sresryYLTR8aCp2ZCR82kfQKaUrqLxeFBVpVI2Yw7_I/edit?usp=sharing"
            
            @st.cache_data(ttl=3600)
            def get_data():
                return load_sheet_data(client, SPREADSHEET_URL)
            
            df = get_data()
            
            if df is None or df.empty:
                st.warning("Nenhum dado disponível")
                return
            
            # Contador de registros (discreto no canto superior direito)
            total_registros = f"{len(df):,}".replace(",", ".")
            st.markdown(
                f"""
                <div style='
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: #f8f9fa;
                    padding: 5px 12px;
                    border-radius: 15px;
                    font-size: 12px;
                    color: #666;
                    border: 1px solid #e9ecef;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                '>
                📊 {total_registros} registros
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Busca de cliente - interface limpa
            st.subheader("🔎 Buscar Cliente")
            
            # Verifica se as colunas necessárias existem
            if "CLIENTES" not in df.columns:
                st.warning("Coluna 'CLIENTES' não encontrada na planilha")
                return
                
            clientes_disponiveis = sorted(df["CLIENTES"].dropna().unique())
            
            if not clientes_disponiveis:
                st.warning("Nenhum cliente cadastrado")
                return
                
            cliente = st.selectbox(
                "Selecione um cliente:",
                clientes_disponiveis,
                key="cliente_select"
            )
            
            if cliente:
                # Encontra o cliente
                cliente_data = df[df["CLIENTES"] == cliente]
                if not cliente_data.empty:
                    row = cliente_data.iloc[0]
                    
                    # Exibe informações em card elegante
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
                                    <span style='font-size:18px; font-weight:600;'>{row.get('NOVO CONSULTOR', 'Não informado')}</span>
                                </p>
                                <hr style='border: 0.5px solid #444; margin: 15px 0;'>
                                <p style='font-size:16px; margin: 10px 0; line-height: 1.4;'>
                                    <strong style='color:#2196F3; font-size:14px;'>🏢 REVENDA:</strong><br>
                                    <span style='font-size:18px; font-weight:600;'>{row.get('REVENDA', 'Não informada')}</span>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        # Informações adicionais (se houver mais colunas)
                        st.info("💡 Selecione um cliente para visualizar as informações completas")
                        
            else:
                st.info("👆 Selecione um cliente na lista acima")
            
        except Exception:
            st.error("Erro ao carregar a aplicação")
    
    # Rodapé discreto
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 11px; color: #666; margin-top: 30px;'>
        © {datetime.now().year} NORMAQ JCB - Todos os direitos reservados • 
        Versão 1.2.0 • Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
