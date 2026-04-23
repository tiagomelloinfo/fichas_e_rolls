import streamlit as st
from database import init_db, get_recent_logs
import time

# --- Configuration ---
st.set_page_config(page_title="Lobby - RPG Manager", page_icon="🎲", initial_sidebar_state="expanded")
init_db()

# --- CSS ---
st.markdown("""
    <style>
    .main { background-color: #1a1c24; color: #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

st.title("🎲 Gestor de RPG de Mesa")

if 'player_name_locked' not in st.session_state:
    st.session_state.player_name_locked = ""

if not st.session_state.player_name_locked:
    st.subheader("Bojnas-vindas, Viajante!")
    st.write("Antes de explorarmos as masmorras, como devemos chamá-lo?")
    
    temp_name = st.text_input("Nome do Personagem ou Jogador", placeholder="Ex: Mestre, Aurora, Valeros...")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Entrar na Aventura", type="primary"):
            if temp_name:
                st.session_state.player_name_locked = temp_name.strip().title()
                st.rerun()
            else:
                st.error("O nome é obrigatório.")
    
    st.info("💡 Dica: Se você for o mestre, use o nome 'Mestre' para ter permissões especiais no mapa.")

else:
    st.success(f"🎭 Você está conectado como: **{st.session_state.player_name_locked}**")
    
    st.divider()
    st.write("### 🧭 O que deseja fazer agora?")
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("#### 🎲 Sala de Rolagem\nRole dados, use comandos customizados e veja o histórico global de jogadas.")
        st.page_link("pages/1_Rolagem.py", label="Entrar na Sala", icon="🎲")
    with c2:
        st.info("#### 🗺️ Mapa Tático\nPosicione seu personagem no grid, visualize o campo de batalha e acompanhe os monstros do Mestre.")
        st.page_link("pages/2_Mapa.py", label="Abrir Mapa", icon="🗺️")

    st.write("⬅️ Utilize o menu na **barra lateral esquerda** para navegar entre as salas.")
    
    if st.button("Sair / Trocar Personagem"):
        st.session_state.player_name_locked = ""
        st.rerun()

# --- Shared Notification System (even in Lobby) ---
if 'last_seen_log_id' not in st.session_state:
    recent = get_recent_logs(1)
    st.session_state.last_seen_log_id = recent[0][0] if recent else 0

if 'toasts_queue' not in st.session_state:
    st.session_state.toasts_queue = {}

def check_for_new_rolls():
    now = time.time()
    recent_logs = get_recent_logs(5)
    if recent_logs:
        for log in reversed(recent_logs):
            log_id, p, roll, res, time_str = log
            if log_id > st.session_state.last_seen_log_id:
                clean_res = res.split('(')[0].strip() if '(' in res else res
                msg = f"🎲 **{p}** rolou **{roll}**\n\nTotal: **{clean_res}**"
                st.session_state.toasts_queue[log_id] = (msg, now)
                st.session_state.last_seen_log_id = log_id
    for lid, (msg, ts) in list(st.session_state.toasts_queue.items()):
        if now - ts < 10: st.toast(msg)

if st.session_state.player_name_locked:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, limit=None, key="lobby_refresh")
    check_for_new_rolls()
