import streamlit as st
import random
import pandas as pd
from database import init_db, add_character, get_all_characters, get_character_by_id, update_character, delete_character, add_dice_log, get_recent_logs

import re

# --- Configuration ---
st.set_page_config(page_title="Old Dragon 2 Manager", page_icon="🐉", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .main { background-color: #1a1c24; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
    .roll-log { font-family: 'Courier New', Courier, monospace; font-size: 0.9em; background: #2d2d2d; padding: 10px; border-radius: 5px; }
    .modifier { font-size: 0.8em; color: #888; }
    </style>
""", unsafe_allow_html=True)

# --- Helpers ---
def get_modifier(val):
    if val <= 5: return -2
    if val <= 8: return -1
    if val <= 12: return 0
    if val <= 15: return 1
    if val <= 18: return 2
    return 3 # 19-20

def get_base_jp(level):
    # OD2 Rule: Starts at 5, increases every 2 levels (3, 5, 7...)
    return 5 + ((level - 1) // 2)

def roll_dice(sides, modifier=0):
    result = random.randint(1, sides)
    total = result + modifier
    return result, total

def parse_custom_roll(roll_str):
    # Regex for standard dice notation: [num]d[sides][+/-][mod]
    pattern = r'^(\d+)?d(\d+)([+-]\d+)?$'
    clean_str = roll_str.replace(" ", "").lower()
    match = re.match(pattern, clean_str)
    
    if match:
        num = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        mod = int(match.group(3)) if match.group(3) else 0
        
        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls) + mod
        
        # Detail string for the log
        rolls_str = ' + '.join(map(str, rolls))
        mod_str = f" {mod:+}" if mod != 0 else ""
        details = f"{total} ({rolls_str}{mod_str})"
        return details
    return None

# --- Initialization ---
init_db()

# --- App Title ---
st.title("🐉 Old Dragon 2 - Gerenciador de Campanha")

# --- Sidebar for Player Name ---
player_name = st.sidebar.text_input("Seu Nome de Jogador", value="Mestre")

# --- Main Tabs ---
tab_fichas, tab_dados = st.tabs(["📋 Fichas de Personagem", "🎲 Rolagem de Dados"])

# --- TAB: FICHAS ---
with tab_fichas:
    col_list, col_details = st.columns([1, 2])

    with col_list:
        st.subheader("Meus Personagens")
        chars = get_all_characters()
        if not chars:
            st.write("Nenhum personagem criado.")
        
        char_options = {f"{c[1]} ({c[2]} Lvl {c[3]})": c[0] for c in chars}
        selected_char_label = st.radio("Selecione para ver/editar", ["+ Novo Personagem"] + list(char_options.keys()))
        
        selected_id = char_options.get(selected_char_label) if selected_char_label != "+ Novo Personagem" else None

    with col_details:
        if selected_id:
            char_data = get_character_by_id(selected_id)
            st.subheader(f"Ficha: {char_data['name']}")
            
            with st.form("edit_char_form"):
                c1, c2, c3 = st.columns(3)
                name = c1.text_input("Nome", char_data['name'])
                race = c2.text_input("Raça", char_data['race'])
                char_class = c3.selectbox("Classe", ["Guerreiro", "Mago", "Clérigo", "Ladino"], index=["Guerreiro", "Mago", "Clérigo", "Ladino"].index(char_data['char_class']))
                
                c4, c5, c6 = st.columns(3)
                level = c4.number_input("Nível", 1, 20, char_data['level'])
                alignment = c5.selectbox("Alinhamento", ["Ordeiro", "Neutro", "Caótico"], index=["Ordeiro", "Neutro", "Caótico"].index(char_data['alignment']))
                xp = c6.number_input("XP", 0, 1000000, char_data['xp'])

                st.divider()
                st.write("### Atributos")
                a1, a2, a3, a4, a5, a6 = st.columns(6)
                str_v = a1.number_input("FOR", 3, 20, char_data['str_val'])
                dex_v = a2.number_input("DES", 3, 20, char_data['dex_val'])
                con_v = a3.number_input("CON", 3, 20, char_data['con_val'])
                int_v = a4.number_input("INT", 3, 20, char_data['int_val'])
                wis_v = a5.number_input("SAB", 3, 20, char_data['wis_val'])
                cha_v = a6.number_input("CAR", 3, 20, char_data['cha_val'])
                
                # Show modifiers
                a1.caption(f"Mod: {get_modifier(str_v):+}")
                a2.caption(f"Mod: {get_modifier(dex_v):+}")
                a3.caption(f"Mod: {get_modifier(con_v):+}")
                a4.caption(f"Mod: {get_modifier(int_v):+}")
                a5.caption(f"Mod: {get_modifier(wis_v):+}")
                a6.caption(f"Mod: {get_modifier(cha_v):+}")

                st.divider()
                st.write("### Combate & Proteção")
                
                # Calculations for JPs
                base_jp = get_base_jp(level)
                final_jp_f = base_jp + get_modifier(con_v)
                final_jp_m = base_jp + get_modifier(wis_v)
                final_jp_e = base_jp + get_modifier(dex_v)

                p1, p2, p3, p4 = st.columns(4)
                hp_m = p1.number_input("PV Máx", 1, 200, char_data['hp_max'])
                hp_c = p2.number_input("PV Atual", 0, 200, char_data['hp_current'])
                ac = p3.number_input("CA", 0, 30, char_data['ac'])
                ba = p4.number_input("BA", 0, 20, char_data['ba'])
                
                st.write(f"**Valor Base de JP (Nível {level}): {base_jp}**")
                j1, j2, j3 = st.columns(3)
                # Displaying JPs as disabled inputs (read-only)
                jp_f = j1.number_input("JP Física (Base + CON)", value=final_jp_f, disabled=True)
                jp_m = j2.number_input("JP Mental (Base + SAB)", value=final_jp_m, disabled=True)
                jp_e = j3.number_input("JP Esquiva (Base + DES)", value=final_jp_e, disabled=True)

                st.divider()
                inventory = st.text_area("Inventário", char_data['inventory'])
                
                m1, m2, m3 = st.columns(3)
                po = m1.number_input("PO", 0, 999999, char_data['gold_po'])
                pp = m2.number_input("PP", 0, 999999, char_data['gold_pp'])
                pc = m3.number_input("PC", 0, 999999, char_data['gold_pc'])

                notes = st.text_area("Notas", char_data['notes'])

                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.form_submit_button("💾 Salvar Alterações"):
                    updated_data = {
                        "name": name, "race": race, "char_class": char_class, "level": level, "alignment": alignment, "xp": xp,
                        "str_val": str_v, "dex_val": dex_v, "con_val": con_v, "int_val": int_v, "wis_val": wis_v, "cha_val": cha_v,
                        "hp_max": hp_m, "hp_current": hp_c, "ac": ac, "ba": ba,
                        "jp_physical": jp_f, "jp_mental": jp_m, "jp_evasion": jp_e,
                        "inventory": inventory, "gold_po": po, "gold_pp": pp, "gold_pc": pc, "notes": notes
                    }
                    update_character(selected_id, updated_data)
                    st.success("Ficha atualizada!")
                    st.rerun()
                
                if col_btn2.form_submit_button("🗑️ Deletar Personagem"):
                    delete_character(selected_id)
                    st.warning("Personagem removido.")
                    st.rerun()
        else:
            st.subheader("✨ Criar Novo Personagem")
            with st.form("new_char_form"):
                nc1, nc2, nc3 = st.columns(3)
                new_name = nc1.text_input("Nome do Personagem")
                new_race = nc2.selectbox("Raça", ["Humano", "Elfo", "Anão", "Halfling"])
                new_class = nc3.selectbox("Classe", ["Guerreiro", "Mago", "Clérigo", "Ladino"])
                
                if st.form_submit_button("Criar Ficha"):
                    if new_name:
                        init_data = {
                            "name": new_name, "race": new_race, "char_class": new_class, "level": 1, "alignment": "Neutro", "xp": 0,
                            "str_val": 10, "dex_val": 10, "con_val": 10, "int_val": 10, "wis_val": 10, "cha_val": 10,
                            "hp_max": 10, "hp_current": 10, "ac": 10, "ba": 0,
                            "jp_physical": 15, "jp_mental": 15, "jp_evasion": 15,
                            "inventory": "", "gold_po": 0, "gold_pp": 0, "gold_pc": 0, "notes": ""
                        }
                        add_character(init_data)
                        st.success(f"{new_name} entrou na aventura!")
                        st.rerun()
                    else:
                        st.error("Dê um nome ao herói!")

# --- TAB: DADOS ---
with tab_dados:
    st.subheader("🎲 Sala de Rolagem")
    
    c_roll, c_log = st.columns([1, 1])
    
    with c_roll:
        st.write("### Rolar Dados")
        dice_mod = st.number_input("Modificador Geral", value=0)
        
        cols = st.columns(3)
        dice_types = [4, 6, 8, 10, 12, 20, 100]
        
        for i, sides in enumerate(dice_types):
            with cols[i % 3]:
                if st.button(f"d{sides}"):
                    val, total = roll_dice(sides, dice_mod)
                    result_str = f"{total} ({val}{dice_mod:+})" if dice_mod != 0 else f"{val}"
                    add_dice_log(player_name, f"d{sides}", result_str)
                    st.toast(f"Resultado: {result_str}")

        custom_roll = st.text_input("Rolagem Customizada (ex: 2d6+3)", "")
        if st.button("Rolar Customizado"):
             if custom_roll:
                 result_details = parse_custom_roll(custom_roll)
                 if result_details:
                     add_dice_log(player_name, custom_roll, result_details)
                     st.toast(f"Resultado: {result_details}")
                     st.rerun()
                 else:
                     st.error("Formato inválido! Use algo como 2d6, 1d20+5 ou d10-1.")
             else:
                 st.warning("Digite uma rolagem.")

    with c_log:
        st.write("### 📜 Histórico Global")
        if st.button("🔄 Atualizar Log"):
            st.rerun()
            
        logs = get_recent_logs(15)
        for log in logs:
            p, roll, res, time = log
            st.markdown(f"**{p}** rolou `{roll}` → **{res}** <br><small style='color:grey'>{time}</small>", unsafe_allow_html=True)
            st.divider()

st.sidebar.markdown("---")
st.sidebar.info("Old Dragon 2 Manager v1.0")
