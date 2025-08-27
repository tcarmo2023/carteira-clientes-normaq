import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ——————————————————————————————
#  CONFIGURAÇÃO DA PÁGINA
# ——————————————————————————————
st.set_page_config(
    page_title="Carteira de Clientes Normaq",
    page_icon="🔍",
    layout="wide",
)

# ——————————————————————————————
#  VERIFICAÇÃO PING UPTIMEROBOT (CORRIGIDO)
# ——————————————————————————————
# Movido para dentro do contexto do Streamlit
try:
    params = st.query_params
    if params.get("ping") == "1":
        st.write("ok")
        st.stop()
except:
    pass  # Continua se não conseguir acessar query_params

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
#  FUNÇÃO FLEXÍVEL PARA PEGAR VALORES
# ——————————————————————————————
def get_value(row, col_name, default="Não informado"):
    for col in row.index:
        if col.strip().upper() == col_name.upper():
            return row[col] if row[col] not in [None, ""] else default
    return default

# ——————————————————————————————
#  INTERFACE PRINCIPAL
# ——————————————————————————————
def main():
    st.title("🔍 Carteira de Clientes NORMAQ JCB")

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

        clientes_disponiveis = sorted(df_pagina1["CLIENTES"].dropna().unique())
        cliente = st.selectbox("Selecione um cliente:", clientes_disponiveis, key="cliente_select")

        if cliente:
            cliente_data = df_pagina1[df_pagina1["CLIENTES"] == cliente]
            row = cliente_data.iloc[0]

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
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                if df_pagina2 is not None and not df_pagina2.empty:
                    maquinas_cliente = df_pagina2[df_pagina2["CLIENTES"] == cliente]

                    if not maquinas_cliente.empty:
                        qtd_maquinas = len(maquinas_cliente)

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
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Ajuste da coluna SERIE para remover pontos/virgulas
                        maquinas_cliente["SERIE"] = maquinas_cliente["SERIE"].astype(str).str.replace(r"[.,]", "", regex=True)

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

    # Rodapé
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 11px; color: #666; margin-top: 30px;'>
        © {datetime.now().year} NORMAQ JCB - Todos os direitos reservados • 
        Versão 1.3.1 • Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
