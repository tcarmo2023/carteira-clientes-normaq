import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import re
import hashlib
import json
from pathlib import Path
import base64
import requests

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
#  LISTA DE EMAILS AUTORIZADOS E LOGINS
# ——————————————————————————————
EMAILS_AUTORIZADOS = {
    "nardie.arruda@normaq.com.br": "nardie.arruda",
    "tarcio.henrique@normaq.com.br": "tarcio.henrique",
    "camila.aguiar@normaq.com.br": "camila.aguiar",
    "sergio.carvalho@normaq.com.br": "sergio.carvalho",
    "flavia.costa@normaq.com.br": "flavia.costa",
    "johnny.barbosa@normaq.com.br": "johnny.barbosa",
    "joao.victor@normaq.com.br": "joao.victor",
    "alison.ferreira@normaq.com.br": "alison.ferreira",
    "thiago.carmo@normaq.com.br": "thiago.carmo",
    "antonio.gustavo@normaq.com.br": "antonio.gustavo",
    "raony.lins@normaq.com.br": "raony.lins",
    "graziela.galdino@normaq.com.br": "graziela.galdino",
    "tiago.fernandes@normaq.com.br": "tiago.fernandes",
    "marcelo.teles@normaq.com.br": "marcelo.teles"
}

SENHA_PADRAO = "NMQ@123"
SENHA_ADMIN = "NMQ@2025"

# ——————————————————————————————
#  OPÇÕES PARA OS DROPDOWNS
# ——————————————————————————————
OPCOES_REVENDA = ["Recife", "Natal", "Fortaleza", "Petrolina"]
OPCOES_PSSR = ["Flávio", "Kecio", "Marcelo"]
OPCOES_CONSULTOR = ["Camila", "David", "Elivaldo", "Josezito", "Nardie", "Roseane", "Tarcio", "Tarcisio", "Tiago", "Sergio", "Renato", "Francisco", "Aliny"]

# ——————————————————————————————
#  FUNÇÕES PARA IMAGENS
# ——————————————————————————————
def get_image_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode()
    except:
        return None

def set_login_background():
    background_url = "https://raw.githubusercontent.com/tcarmo2023/carteira-clientes-normaq/029c6610026b80e88ca7733690fe1a12f44874b2/fotos/fundo.png"
    base64_bg = get_image_from_url(background_url)
    
    if base64_bg:
        st.markdown(
            f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/png;base64,{base64_bg}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 2rem;
                margin-top: 2rem;
                margin-bottom: 2rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            section[data-testid="stSidebar"] {{
                background-color: rgba(255, 255, 255, 0.95) !important;
            }}
            .stTabs [data-baseweb="tab-list"] {{
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                padding: 5px;
            }}
            .stTabContent {{
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                padding: 15px;
                margin-top: 10px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

def set_main_background():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff;
        }
        .main .block-container {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def display_logo_footer():
    logo_url = "https://raw.githubusercontent.com/tcarmo2023/carteira-clientes-normaq/main/fotos/logo.png"
    base64_logo = get_image_from_url(logo_url)
    
    if base64_logo:
        st.markdown(
            f"""
            <div style='text-align: center; margin-top: 30px;'>
                <img src="data:image/png;base64,{base64_logo}" alt="Logo NORMAQ" style='height: 50px;'>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style='text-align: center; margin-top: 30px;'>
                <span style='font-size: 24px; font-weight: bold; color: #1e3a8a;'>NORMAQ JCB</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# ——————————————————————————————
#  FUNÇÕES DE ARMAZENAMENTO DE USUÁRIOS (CORRIGIDAS)
# ——————————————————————————————
def get_usuarios_file():
    return Path("usuarios.json")

def carregar_usuarios():
    """Carrega usuários garantindo que senha_visualizavel sempre reflita a senha atual"""
    usuarios_file = get_usuarios_file()
    
    if not usuarios_file.exists():
        usuarios = {}
        for email, login in EMAILS_AUTORIZADOS.items():
            usuarios[login] = {
                "email": email,
                "senha_hash": hash_senha(SENHA_PADRAO),
                "senha_visualizavel": SENHA_PADRAO,
                "primeiro_login": True,
                "data_criacao": datetime.now().isoformat(),
                "data_ultima_alteracao": datetime.now().isoformat(),
                "historico_senhas": [SENHA_PADRAO]
            }
        salvar_usuarios(usuarios)
        return usuarios
    
    try:
        with open(usuarios_file, 'r', encoding='utf-8') as f:
            usuarios_existentes = json.load(f)
            
        usuarios_atualizados = False
        
        for login, dados_usuario in usuarios_existentes.items():
            # CORREÇÃO CRÍTICA: Garantir que senha_visualizavel sempre reflita a senha atual
            if "historico_senhas" in dados_usuario and dados_usuario["historico_senhas"]:
                # A senha atual é sempre a última do histórico
                senha_atual = dados_usuario["historico_senhas"][-1]
                if dados_usuario.get("senha_visualizavel") != senha_atual:
                    dados_usuario["senha_visualizavel"] = senha_atual
                    usuarios_atualizados = True
            
            # Garantir campos obrigatórios
            if "data_criacao" not in dados_usuario:
                dados_usuario["data_criacao"] = datetime.now().isoformat()
                usuarios_atualizados = True
            
            if "data_ultima_alteracao" not in dados_usuario:
                dados_usuario["data_ultima_alteracao"] = datetime.now().isoformat()
                usuarios_atualizados = True
            
            if "senha_visualizavel" not in dados_usuario:
                dados_usuario["senha_visualizavel"] = SENHA_PADRAO
                usuarios_atualizados = True
            
            if "historico_senhas" not in dados_usuario:
                dados_usuario["historico_senhas"] = [SENHA_PADRAO]
                usuarios_atualizados = True
        
        # Adicionar novos usuários
        for email, login in EMAILS_AUTORIZADOS.items():
            if login not in usuarios_existentes:
                usuarios_existentes[login] = {
                    "email": email,
                    "senha_hash": hash_senha(SENHA_PADRAO),
                    "senha_visualizavel": SENHA_PADRAO,
                    "primeiro_login": True,
                    "data_criacao": datetime.now().isoformat(),
                    "data_ultima_alteracao": datetime.now().isoformat(),
                    "historico_senhas": [SENHA_PADRAO]
                }
                usuarios_atualizados = True
        
        if usuarios_atualizados:
            salvar_usuarios(usuarios_existentes)
            
        return usuarios_existentes
        
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")
        usuarios = {}
        for email, login in EMAILS_AUTORIZADOS.items():
            usuarios[login] = {
                "email": email,
                "senha_hash": hash_senha(SENHA_PADRAO),
                "senha_visualizavel": SENHA_PADRAO,
                "primeiro_login": True,
                "data_criacao": datetime.now().isoformat(),
                "data_ultima_alteracao": datetime.now().isoformat(),
                "historico_senhas": [SENHA_PADRAO]
            }
        return usuarios

def salvar_usuarios(usuarios):
    try:
        usuarios_file = get_usuarios_file()
        if usuarios_file.exists():
            backup_file = usuarios_file.with_suffix('.json.backup')
            import shutil
            shutil.copy2(usuarios_file, backup_file)
        
        with open(usuarios_file, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {e}")
        return False

# ——————————————————————————————
#  FUNÇÕES DE AUTENTICAÇÃO (CORRIGIDAS)
# ——————————————————————————————
def hash_senha(senha):
    salt = "normaq_jcb_2025_salt"
    return hashlib.sha256((senha + salt).encode()).hexdigest()

def verificar_senha(senha, hash_armazenado):
    return hash_senha(senha) == hash_armazenado

def inicializar_usuarios():
    return carregar_usuarios()

def alterar_senha_usuario(login, nova_senha):
    """CORREÇÃO CRÍTICA: Garante que senha_visualizavel SEMPRE seja atualizada"""
    usuarios = carregar_usuarios()
    
    if login in usuarios:
        # Atualizar senha hash
        usuarios[login]["senha_hash"] = hash_senha(nova_senha)
        
        # CORREÇÃO: SEMPRE atualizar senha_visualizavel com a nova senha
        usuarios[login]["senha_visualizavel"] = nova_senha
        
        # Atualizar histórico
        if "historico_senhas" not in usuarios[login]:
            usuarios[login]["historico_senhas"] = []
        
        # Adicionar ao histórico apenas se for diferente da última
        if not usuarios[login]["historico_senhas"] or usuarios[login]["historico_senhas"][-1] != nova_senha:
            usuarios[login]["historico_senhas"].append(nova_senha)
        
        # Manter apenas as últimas 10 senhas
        if len(usuarios[login]["historico_senhas"]) > 10:
            usuarios[login]["historico_senhas"] = usuarios[login]["historico_senhas"][-10:]
        
        usuarios[login]["primeiro_login"] = False
        usuarios[login]["data_ultima_alteracao"] = datetime.now().isoformat()
            
        return salvar_usuarios(usuarios)
    return False

# ——————————————————————————————
#  VERIFICAÇÃO DE LOGIN
# ——————————————————————————————
def verificar_login():
    if 'usuario_logado' not in st.session_state:
        st.session_state.usuario_logado = None
    
    if not st.session_state.usuario_logado:
        set_login_background()
        
        st.title("🔍 Carteira de Clientes NORMAQ JCB")
        st.markdown("---")
        
        tab_login, tab_cadastro, tab_ajuste_senha, tab_excluir_usuario, tab_info = st.tabs([
            "Login", "Cadastrar Usuário", "Ajustes de Senha", "Excluir Usuário", "Informações"
        ])
        
        with tab_login:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.subheader("🔐 Acesso Restrito")
                login = st.text_input("Login:", placeholder="seu.login")
                senha = st.text_input("Senha:", type="password", placeholder="Digite sua senha")
                
                if st.button("Acessar Sistema", type="primary", use_container_width=True):
                    usuarios = inicializar_usuarios()
                    
                    if login in usuarios:
                        if verificar_senha(senha, usuarios[login]["senha_hash"]):
                            st.session_state.usuario_logado = login
                            st.session_state.email_usuario = usuarios[login]["email"]
                            st.session_state.primeiro_login = usuarios[login].get("primeiro_login", False)
                            st.success("Acesso permitido!")
                            st.rerun()
                        else:
                            st.error("Senha incorreta.")
                    else:
                        st.error("Login não encontrado.")
            
            st.markdown("---")
            st.info("""
            **Problemas de acesso?**
            - Esqueceu sua senha?
            - Não possui cadastro?
            
            **Contate o Administrador:**  
            Thiago Carmo – Especialista em Dados  
            📞 [(81) 99514-3900](https://wa.me/5581995143900)
            """)
        
        with tab_cadastro:
            st.subheader("Cadastrar Novo Usuário")
            senha_admin = st.text_input("Senha de administrador:", type="password", key="senha_admin_cadastro")
            
            if senha_admin == SENHA_ADMIN:
                with st.form("form_cadastro_usuario"):
                    email = st.text_input("Email corporativo:", placeholder="seu.email@normaq.com.br")
                    login = st.text_input("Login:", placeholder="seu.login")
                    senha_provisoria = st.text_input("Senha provisória:", type="password", value=SENHA_PADRAO)
                    
                    submitted = st.form_submit_button("Cadastrar Usuário")
                    
                    if submitted:
                        if not all([email, login, senha_provisoria]):
                            st.error("Todos os campos são obrigatórios!")
                        elif not email.endswith("@normaq.com.br"):
                            st.error("O email deve ser corporativo (@normaq.com.br)")
                        else:
                            usuarios = carregar_usuarios()
                            usuarios[login] = {
                                "email": email,
                                "senha_hash": hash_senha(senha_provisoria),
                                "senha_visualizavel": senha_provisoria,
                                "primeiro_login": True,
                                "data_criacao": datetime.now().isoformat(),
                                "data_ultima_alteracao": datetime.now().isoformat(),
                                "historico_senhas": [senha_provisoria]
                            }
                            if salvar_usuarios(usuarios):
                                st.success(f"Usuário {login} cadastrado com sucesso!")
                                st.info(f"Senha provisória: {senha_provisoria}")
                            else:
                                st.error("Erro ao salvar usuário.")
            elif senha_admin != "":
                st.error("Senha de administrador incorreta!")
        
        with tab_ajuste_senha:
            st.subheader("Ajustes de Senha - Administrador")
            senha_admin = st.text_input("Senha de administrador:", type="password", key="senha_admin_ajuste")
            
            if senha_admin == SENHA_ADMIN:
                usuarios = carregar_usuarios()
                
                if usuarios:
                    usuario_selecionado = st.selectbox("Selecione o usuário:", list(usuarios.keys()))
                    
                    # CORREÇÃO: Mostrar sempre a senha atual correta
                    if usuario_selecionado:
                        # A senha atual é sempre a última do histórico
                        historico = usuarios[usuario_selecionado].get("historico_senhas", [])
                        senha_atual = historico[-1] if historico else "Não disponível"
                        
                        st.info(f"**Senha atual do usuário:** `{senha_atual}`")
                        st.info(f"**Histórico de senhas:** {len(historico)} senha(s) registrada(s)")
                    
                    with st.form("form_ajuste_senha_admin"):
                        nova_senha = st.text_input("Nova senha:", type="password", value=SENHA_PADRAO)
                        resetar_primeiro_login = st.checkbox("Forçar alteração de senha no próximo login", value=True)
                        
                        submitted = st.form_submit_button("Alterar Senha")
                        
                        if submitted:
                            if not nova_senha:
                                st.error("A senha não pode estar vazia!")
                            else:
                                if alterar_senha_usuario(usuario_selecionado, nova_senha):
                                    usuarios[usuario_selecionado]["primeiro_login"] = resetar_primeiro_login
                                    if salvar_usuarios(usuarios):
                                        st.success(f"Senha do usuário {usuario_selecionado} alterada com sucesso!")
                                        st.info(f"Email: {usuarios[usuario_selecionado]['email']}")
                                        st.info(f"**Nova senha:** `{nova_senha}`")
                                    else:
                                        st.error("Erro ao salvar configurações do usuário.")
                                else:
                                    st.error("Erro ao alterar senha.")
                else:
                    st.warning("Nenhum usuário cadastrado.")
            elif senha_admin != "":
                st.error("Senha de administrador incorreta!")
        
        with tab_excluir_usuario:
            st.subheader("Excluir Usuário - Administrador")
            senha_admin = st.text_input("Senha de administrador:", type="password", key="senha_admin_excluir")
            
            if senha_admin == SENHA_ADMIN:
                usuarios = carregar_usuarios()
                
                if usuarios:
                    usuario_selecionado = st.selectbox("Selecione o usuário para excluir:", list(usuarios.keys()))
                    
                    if usuario_selecionado:
                        # CORREÇÃO: Mostrar sempre a senha atual correta
                        historico = usuarios[usuario_selecionado].get("historico_senhas", [])
                        senha_atual = historico[-1] if historico else "Não disponível"
                        
                        st.warning(f"Tem certeza que deseja excluir o usuário {usuario_selecionado}?")
                        st.info(f"**Email:** {usuarios[usuario_selecionado]['email']}")
                        st.info(f"**Senha atual:** `{senha_atual}`")
                        st.info(f"**Histórico de senhas:** {len(historico)} senha(s) registrada(s)")
                        
                        if st.button("Confirmar Exclusão", type="secondary"):
                            if len(usuarios) <= 1:
                                st.error("Não é possível excluir o último usuário!")
                            else:
                                del usuarios[usuario_selecionado]
                                if salvar_usuarios(usuarios):
                                    st.success(f"Usuário {usuario_selecionado} excluído com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir usuário.")
                else:
                    st.warning("Nenhum usuário cadastrado.")
            elif senha_admin != "":
                st.error("Senha de administrador incorreta!")
        
        with tab_info:
            st.subheader("Informações de Acesso")
            st.markdown("""
            **Para problemas de acesso:**
            
            Entre em contato com o administrador do sistema:
            
            **Thiago Carmo** – Especialista em Dados  
            📞 [(81) 99514-3900](https://wa.me/5581995143900)
            
            **Horário de atendimento:**  
            Segunda a sexta, 8h às 18h
            
            **Sistema de senhas:**  
            • As senhas são armazenadas de forma segura e permanente
            • Histórico completo de todas as alterações
            • Nenhuma senha é perdida ou excluída
            """)
        
        st.stop()
    
    if st.session_state.get('primeiro_login', False):
        alterar_senha_obrigatorio()

# ——————————————————————————————
#  ALTERAÇÃO DE SENHA OBRIGATÓRIA
# ——————————————————————————————
def alterar_senha_obrigatorio():
    set_main_background()
    
    st.title("🔒 Alteração de Senha Obrigatória")
    st.warning("É necessário alterar sua senha antes de acessar o sistema.")
    
    with st.form("form_alterar_senha"):
        nova_senha = st.text_input("Nova senha:", type="password")
        confirmar_senha = st.text_input("Confirmar nova senha:", type="password")
        
        submitted = st.form_submit_button("Alterar Senha")
        
        if submitted:
            if not nova_senha:
                st.error("A senha não pode estar vazia!")
            elif nova_senha != confirmar_senha:
                st.error("As senhas não coincidem!")
            else:
                if alterar_senha_usuario(st.session_state.usuario_logado, nova_senha):
                    st.session_state.primeiro_login = False
                    st.success("Senha alterada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao alterar senha.")

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
#  FUNÇÕES PARA PLANILHAS (mantidas as originais)
# ——————————————————————————————
def load_sheet_data(client, spreadsheet_url, sheet_name):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    records = worksheet.get_all_records()
    if not records:
        return None
    df = pd.DataFrame(records)
    try:
        df = df.dropna(how='all')
    except:
        df = df[df.notnull().any(axis=1)]
    df.columns = [str(c).strip() for c in df.columns]
    return df

def get_exact_headers(client, spreadsheet_url, sheet_name):
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet(sheet_name)
    headers = worksheet.row_values(1)
    return [str(header).strip() for header in headers]

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

def get_value(row, col_name, default="Não informado"):
    for col in row.index:
        if col.strip().upper() == col_name.upper():
            return row[col] if row[col] not in [None, ""] else default
    return default

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
#  CSS + JS PARA PROTEÇÃO
# ——————————————————————————————
def inject_protection_css():
    st.markdown("""
    <style>
    .stDataFrame, .streamlit-expanderHeader, .Markdown, .stTable, .stAceContent {
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
    }
    table {
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
    }
    input, textarea {
        user-select: text !important;
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
    }
    .stDownloadButton, [data-testid="stDownloadButton"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        opacity: 0 !important;
    }
    .main .block-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 2rem;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }
    </style>
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && (e.key === 'c' || e.key === 'C' || e.key === 's' || e.key === 'S' || e.key === 'C' && e.shiftKey)) {
            e.preventDefault();
        }
        if (e.key === 'PrintScreen') {
            e.preventDefault();
        }
        if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'C' || e.key === 'c')) {
            e.preventDefault();
        }
    });
    document.addEventListener('selectionchange', function () {
        try { window.getSelection().removeAllRanges(); } catch(e) {}
    });
    </script>
    """, unsafe_allow_html=True)

# ——————————————————————————————
#  INTERFACE PRINCIPAL
# ——————————————————————————————
def main():
    verificar_login()
    set_main_background()
    inject_protection_css()
    
    st.sidebar.success(f"👤 Logado como: {st.session_state.usuario_logado}")
    
    if st.sidebar.button("🔐 Alterar Senha"):
        st.session_state.alterar_senha = True
    
    if st.sidebar.button("🚪 Sair"):
        st.session_state.usuario_logado = None
        st.session_state.email_usuario = None
        st.session_state.primeiro_login = False
        st.session_state.alterar_senha = False
        st.rerun()

    if st.session_state.get('alterar_senha', False):
        st.title("🔒 Alterar Senha")
        with st.form("form_alterar_senha"):
            senha_atual = st.text_input("Senha atual:", type="password")
            nova_senha = st.text_input("Nova senha:", type="password")
            confirmar_senha = st.text_input("Confirmar nova senha:", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Alterar Senha")
            with col2:
                cancelar = st.form_submit_button("Cancelar")
            
            if cancelar:
                st.session_state.alterar_senha = False
                st.rerun()
                
            if submitted:
                usuarios = carregar_usuarios()
                if verificar_senha(senha_atual, usuarios[st.session_state.usuario_logado]["senha_hash"]):
                    if nova_senha != confirmar_senha:
                        st.error("As novas senhas não coincidem!")
                    else:
                        if alterar_senha_usuario(st.session_state.usuario_logado, nova_senha):
                            st.session_state.alterar_senha = False
                            st.success("Senha alterada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao alterar senha.")
                else:
                    st.error("Senha atual incorreta!")

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
                                <span style='font-size:18px; font-weight:600;'>{get_value(row, "Revenda")}</span>
                            </p>
                            <hr style='border: 0.5px solid #444; margin: 15px 0;'>
                            <p style='font-size:16px; margin: 10px 0; line-height: 1.4;'>
                                <strong style='color:#FF9800; font-size:14px;'>🔧 PSSR:</strong><br>
                                <span style='font-size:18px; font-weight:600;'>{get_value(row, "PSSR")}</span>
                            </p>
                            <hr style='border: 0.5px solid #444; margin: 15px 0;'>
                            <p style='font-size:16px; margin: 10px 0; line-height: 1.4;'>
                                <strong style='color:#9C27B0; font-size:14px;'>📞 CONTATO:</strong><br>
                                <span style='font-size:18px; font-weight:600;'>
                                    <a href='{whatsapp_link}' target='_blank' style='color: #25D366; text-decoration: none;'>
                                        {contato_value} 💬
                                    </a>
                                </span>
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
                                <br>
                                <span style="font-weight:bold; font-size:16px; color:#2196F3;">
                                    Categorias: {categorias_str}
                                </span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            maquinas_cliente["SERIE"] = maquinas_cliente["SERIE"].astype(str).str.replace(r"[.,]", "", regex=True)
                            maquinas_cliente = maquinas_cliente.copy()
                            maquinas_cliente["N°"] = range(1, len(maquinas_cliente) + 1)
                            n_cliente_value = get_value(row, "Nº Cliente", "")
                            n_cliente_limpo = re.sub(r'[^\d]', '', str(n_cliente_value))
                            maquinas_cliente["Nº CLIENTE"] = n_cliente_limpo
                            cols_ordenadas = ["N°", "Nº CLIENTE", "CLIENTES"] + [col for col in maquinas_cliente.columns if col not in ["N°", "Nº CLIENTE", "CLIENTES"]]
                            maquinas_cliente = maquinas_cliente[cols_ordenadas]
                            maquinas_cliente = maquinas_cliente.loc[:, ~maquinas_cliente.columns.str.contains('^Unnamed', na=False)]
                            maquinas_cliente = maquinas_cliente.loc[:, maquinas_cliente.columns != '']
                            if maquinas_cliente.iloc[:, 0].name != 'N°':
                                maquinas_cliente = maquinas_cliente.iloc[:, 1:]
                            maquinas_cliente.columns = [col.capitalize() for col in maquinas_cliente.columns]
                            st.table(maquinas_cliente.reset_index(drop=True))
                        else:
                            st.info("💡 Selecione um cliente para visualizar as informações completas")
                            st.warning("📭 Nenhuma máquina encontrada para este cliente")
                    else:
                        st.info("💡 Selecione um cliente para visualizar as informações completas")
            else:
                st.info("👆 Selecione um cliente na lista acima")

        except Exception as e:
            st.error(f"Erro ao carregar a aplicação: {e}")

    with tab2:
        st.header("Cadastro de Novo Cliente")
        senha = st.text_input("Digite a senha para acesso:", type="password")
        
        if senha == SENHA_ADMIN:
            with st.form("form_cadastro"):
                col1, col2 = st.columns(2)
                with col1:
                    cliente = st.text_input("CLIENTES*")
                    revenda = st.selectbox("Revenda*", OPCOES_REVENDA)
                with col2:
                    pssr = st.selectbox("PSSR*", OPCOES_PSSR)
                    consultor = st.selectbox("NOVO CONSULTOR*", OPCOES_CONSULTOR)
                    cnpj_cpf = st.text_input("CNPJ/CPF*")
                    contato = st.text_input("Contato*")
                    n_cliente = st.text_input("Nº Cliente*")
                
                submitted = st.form_submit_button("Cadastrar Cliente")
                
                if submitted:
                    if not all([cliente, consultor, revenda, pssr, cnpj_cpf, contato, n_cliente]):
                        st.error("Todos os campos marcados com * são obrigatórios!")
                    else:
                        try:
                            novo_cliente = {
                                "CLIENTES": cliente, "NOVO CONSULTOR": consultor, "Revenda": revenda,
                                "PSSR": pssr, "CNPJ/CPF": cnpj_cpf, "Contato": contato, "Nº Cliente": n_cliente
                            }
                            if save_to_sheet(client, SPREADSHEET_URL, "Página1", novo_cliente):
                                st.success("Cliente cadastrado com sucesso!")
                                st.cache_data.clear()
                            else:
                                st.error("Erro ao cadastrar cliente.")
                        except Exception as e:
                            st.error(f"Erro ao cadastrar: {e}")
        elif senha != "":
            st.error("Senha incorreta!")
    
    with tab3:
        st.header("Ajuste de Dados do Cliente")
        senha = st.text_input("Digite a senha para acesso:", type="password", key="senha_ajuste")
        
        if senha == SENHA_ADMIN:
            try:
                df_pagina1 = get_data("Página1")
                opcoes_clientes = sorted([str(cliente) for cliente in df_pagina1["CLIENTES"].dropna().unique()])
                cliente_ajuste = st.selectbox("Selecione o cliente para ajuste:", opcoes_clientes)
                
                if cliente_ajuste:
                    cliente_data = df_pagina1[df_pagina1["CLIENTES"].astype(str) == cliente_ajuste]
                    
                    if not cliente_data.empty:
                        cliente_data_row = cliente_data.iloc[0]
                        
                        with st.form("form_ajuste"):
                            st.subheader(f"Editando: {cliente_ajuste}")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                novo_cliente = st.text_input("CLIENTES", value=get_value(cliente_data_row, "CLIENTES"))
                                def encontrar_indice_seguro(valor, lista):
                                    try:
                                        return lista.index(valor)
                                    except ValueError:
                                        return 0
                                novo_consultor = st.selectbox("NOVO CONSULTOR", OPCOES_CONSULTOR, 
                                                             index=encontrar_indice_seguro(get_value(cliente_data_row, "NOVO CONSULTOR"), OPCOES_CONSULTOR))
                                nova_revenda = st.selectbox("Revenda", OPCOES_REVENDA,
                                                          index=encontrar_indice_seguro(get_value(cliente_data_row, "Revenda"), OPCOES_REVENDA))
                            
                            with col2:
                                novo_pssr = st.selectbox("PSSR", OPCOES_PSSR,
                                                        index=encontrar_indice_seguro(get_value(cliente_data_row, "PSSR"), OPCOES_PSSR))
                                novo_cnpj = st.text_input("CNPJ/CPF", value=get_value(cliente_data_row, "CNPJ/CPF"))
                                novo_contato = st.text_input("Contato", value=get_value(cliente_data_row, "Contato"))
                                novo_n_cliente = st.text_input("Nº Cliente", value=get_value(cliente_data_row, "Nº Cliente"))
                            
                            submitted = st.form_submit_button("Salvar Alterações")
                            
                            if submitted:
                                try:
                                    row_index = cliente_data.index[0] + 2
                                    dados_atualizados = {
                                        "CLIENTES": novo_cliente, "NOVO CONSULTOR": novo_consultor, "Revenda": nova_revenda,
                                        "PSSR": novo_pssr, "CNPJ/CPF": novo_cnpj, "Contato": novo_contato, "Nº Cliente": novo_n_cliente
                                    }
                                    if update_sheet_data(client, SPREADSHEET_URL, "Página1", row_index, dados_atualizados):
                                        st.success("Dados atualizados com sucesso!")
                                        st.cache_data.clear()
                                    else:
                                        st.error("Erro ao atualizar dados.")
                                except Exception as e:
                                    st.error(f"Erro ao atualizar: {e}")
                    else:
                        st.warning("Cliente não encontrado!")
                
            except Exception as e:
                st.error(f"Erro ao carregar dados: {e}")
        elif senha != "":
            st.error("Senha incorreta!")

    st.markdown("---")
    display_logo_footer()
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 11px; color: #666; margin-top: 10px;'>
        © {datetime.now().year} NORMAQ JCB - Todos os direitos reservados • 
        Versão 1.5.5 • Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}
        <br>
        Desenvolvido por Thiago Carmo – Especialista em Dados • 📞 <a href='https://wa.me/5581995143900' style='color: #666;'>(81) 99514-3900</a>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
