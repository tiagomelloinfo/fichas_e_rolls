import streamlit as st
from database import get_recent_logs, get_map_state, update_map_cell, delete_map_cell, clear_map
from streamlit_autorefresh import st_autorefresh
import time

# --- Configuration ---
st.set_page_config(page_title="Mapa Tático", page_icon="🗺️", layout="wide", initial_sidebar_state="expanded")

# --- CSS ---
st.markdown("""
    <style>
    .map-container {
        position: relative;
        display: inline-block;
        border: 2px solid #444;
        background-color: #222;
        background-size: contain;
        background-repeat: no-repeat;
    }
    .grid-cell {
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7em;
        font-weight: bold;
        cursor: pointer;
        transition: background 0.3s;
        min-height: 50px;
    }
    .grid-cell:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    .occupied {
        background-color: rgba(76, 175, 80, 0.4);
        border: 2px solid #4CAF50;
        color: white;
        text-shadow: 1px 1px 2px black;
    }
    .monster {
        background-color: rgba(244, 67, 54, 0.4);
        border: 2px solid #f44336;
    }
    </style>
""", unsafe_allow_html=True)

# --- Check for Name ---
if 'player_name_locked' not in st.session_state or not st.session_state.player_name_locked:
    st.warning("⚠️ Por favor, defina seu nome na página inicial antes de jogar.")
    st.stop()

player_name = st.session_state.player_name_locked
is_master = player_name.lower() == "mestre"

# --- Global Toasts Logic (Same as other pages) ---
if 'last_seen_log_id' not in st.session_state:
    recent = get_recent_logs(1)
    st.session_state.last_seen_log_id = recent[0][0] if recent else 0

if 'toasts_queue' not in st.session_state:
    st.session_state.toasts_queue = {}

def check_for_new_rolls():
    now = time.time()
    recent_logs = get_recent_logs(10)
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

# --- Refresh and Toast ---
st_autorefresh(interval=3000, limit=None, key="map_refresh")
check_for_new_rolls()

st.title("🗺️ Mapa Tático")

# --- Sidebar Controls ---
st.sidebar.header("Configurações do Mapa")
if is_master:
    if st.sidebar.button("Limpar Todo o Mapa"):
        clear_map()
        st.rerun()
    
    st.sidebar.subheader("🖼️ Imagem do Mapa")
    st.sidebar.caption("💡 Dica: Use imagens quadradas (proporção 1:1). Recomendado: **1200x1200px**.")
    uploaded_file = st.sidebar.file_uploader("Carregar do PC", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        import base64
        bytes_data = uploaded_file.getvalue()
        base64_img = base64.b64encode(bytes_data).decode()
        # Para persistência global simples, vamos salvar num arquivo temporário
        with open("current_map_b64.txt", "w") as f:
            f.write(base64_img)
        st.session_state.map_image_url = f"data:image/jpeg;base64,{base64_img}"
        st.rerun()

    # Tenta carregar imagem salva globalmente se não estiver na sessão
    import os
    if 'map_image_url' not in st.session_state and os.path.exists("current_map_b64.txt"):
        with open("current_map_b64.txt", "r") as f:
            saved_b64 = f.read()
            st.session_state.map_image_url = f"data:image/jpeg;base64,{saved_b64}"

else:
    st.sidebar.info("Apenas o Mestre pode carregar mapas ou limpar o grid.")
    # Jogadores também tentam carregar a imagem salva
    import os
    if os.path.exists("current_map_b64.txt"):
        with open("current_map_b64.txt", "r") as f:
            saved_b64 = f.read()
            st.session_state.map_image_url = f"data:image/jpeg;base64,{saved_b64}"

map_image = st.session_state.get('map_image_url', "")

# --- Map Rendering ---
grid_size = 60 # Aumentado de 24 para 60
map_state = get_map_state()
# Labels: Usando números para ambos para simplificar a visualização densa
cols_labels = [str(i+1) for i in range(grid_size)]
rows_labels = [str(i+1) for i in range(grid_size)]

st.write(f"### Grid de Combate ({grid_size}x{grid_size})")

# CSS dinâmico para o fundo do mapa
if map_image:
    st.markdown(f"""
        <style>
        [data-testid="stHorizontalBlock"] {{
            background-image: url('{map_image}');
            background-size: cover;
            background-position: center;
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #444;
            gap: 0px !important;
        }}
        .stButton > button {{
            background-color: rgba(30, 30, 30, 0.4) !important;
            color: white !important;
            border: 0.1px solid rgba(255,255,255,0.1) !important;
            height: 18px !important;
            padding: 0px !important;
            font-size: 0.5em !important;
            min-width: 0px !important;
        }}
        .stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.2) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# Renderização do Grid
main_cols = st.columns(grid_size)
for i, col_label in enumerate(cols_labels):
    with main_cols[i]:
        # Para um grid de 60, mostrar o label da coluna apenas no topo
        st.write(f"<p style='font-size:0.6em; text-align:center; margin:0;'>{col_label}</p>", unsafe_allow_html=True)
        for row_label in rows_labels:
            cell_id = f"C{col_label}R{row_label}"
            cell_data = map_state.get(cell_id)
            
            label = ""
            if cell_data:
                label = cell_data['label']
                # Cores baseadas no tipo
                color = cell_data.get('color', 'green')
                bg_color = "rgba(76, 175, 80, 0.7)" if color == "green" else "rgba(244, 67, 54, 0.7)"
                if color == "blue": bg_color = "rgba(33, 150, 243, 0.7)"
                
                # Injetar estilo específico para este botão ocupado
                st.markdown(f"""
                    <style>
                    button[key*="{cell_id}"] {{
                        background-color: {bg_color} !important;
                        border: 2px solid white !important;
                    }}
                    </style>
                """, unsafe_allow_html=True)
            
            if st.button(label if label else " ", key=cell_id, use_container_width=True):
                if cell_data and (is_master or cell_data['player'] == player_name):
                    delete_map_cell(cell_id)
                    st.rerun()
                elif not cell_data:
                    if is_master:
                        st.session_state.placing_cell = cell_id
                        st.rerun()
                    else:
                        update_map_cell(cell_id, player_name, "green", player_name)
                        st.rerun()

# Master placement dialog
if is_master and 'placing_cell' in st.session_state:
    cell_to_place = st.session_state.placing_cell
    with st.form("place_form"):
        st.write(f"Colocando entidade em **{cell_to_place}**")
        entity_name = st.text_input("Nome da Entidade", "Monstro")
        is_monster = st.checkbox("É um Monstro?", value=True)
        if st.form_submit_button("Confirmar"):
            color = "red" if is_monster else "blue"
            update_map_cell(cell_to_place, entity_name, color, player_name)
            del st.session_state.placing_cell
            st.rerun()
        if st.form_submit_button("Cancelar"):
            del st.session_state.placing_cell
            st.rerun()

st.sidebar.divider()
st.sidebar.write("### Legenda")
st.sidebar.write("🟢 Seus Personagens")
st.sidebar.write("🔴 Monstros/Inimigos")
st.sidebar.write("⚪ Outros Jogadores")
