import streamlit as st
import random
import pandas as pd
from datetime import datetime
from database import init_db, add_character, get_all_characters, get_character_by_id, update_character, delete_character, add_dice_log, get_recent_logs
from streamlit_autorefresh import st_autorefresh

import re

# --- Configuration ---
st.set_page_config(page_title="Rolagem de Dados", page_icon="🎲", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .main { background-color: #1a1c24; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; }
    .roll-log { font-family: 'Courier New', Courier, monospace; font-size: 0.9em; background: #2d2d2d; padding: 10px; border-radius: 5px; }
    .modifier { font-size: 0.8em; color: #888; }
    /* Newest log base style */
    .log-entry {
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid transparent;
        transition: border-color 0.5s;
    }
    .log-entry-highlighted {
        border-left: 4px solid #4CAF50;
    }
    .dice-square {
        display: inline-block;
        border: 1px solid #4CAF50;
        border-radius: 4px;
        padding: 2px 6px;
        margin: 2px;
        font-family: 'Courier New', Courier, monospace;
        background-color: #262730;
        color: #4CAF50;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Helpers ---
def get_modifier(val):
    if val <= 3: return -3
    if val <= 5: return -2
    if val <= 8: return -1
    if val <= 12: return 0
    if val <= 14: return 1
    if val <= 16: return 2
    if val <= 18: return 3
    return 4 # 19-20

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
        mod_str = f" + MOD:{mod:+}" if mod != 0 else ""
        details = f"{total} ({rolls_str}{mod_str})"
        return details
    return None

# --- Initialization ---
init_db()

# --- App Title ---
st.title("🎲 Rolagem de Dados")

# --- Sidebar Configuration ---
st.sidebar.info("Rolagem de Dados")
st.sidebar.markdown("---")

# --- ROLAGEM DE DADOS ---
# Auto-refresh every 3 seconds to keep history updated and match animation
st_autorefresh(interval=3000, limit=None, key="dice_refresh")

st.subheader("🎲 Sala de Rolagem")

# Player Name Input on the main page
player_name = st.text_input("Seu Nome de Personagem / Jogador", value="Mestre")

st.divider()

c_roll, c_log = st.columns([1, 1])

with c_roll:
    st.write("### Rolar Dados")
    dice_mod = st.number_input("Modificador Geral", value=0)
    
    cols = st.columns(3)
    dice_types = [4, 6, 8, 10, 12, 20, 100]
    
    for i, sides in enumerate(dice_types):
        with cols[i % 3]:
            if st.button(f"Lançar d{sides}", key=f"btn_d{sides}"):
                val, total = roll_dice(sides, dice_mod)
                result_str = f"{total} ({val} + MOD:{dice_mod:+})" if dice_mod != 0 else f"{val}"
                add_dice_log(player_name, f"d{sides}", result_str)
                st.toast(f"Resultado: {result_str}")

    with st.form("custom_roll_form", clear_on_submit=True):
        custom_roll = st.text_input("Rolagem Customizada (ex: 2d6+3)", "")
        if st.form_submit_button("Rolar Customizado"):
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
    
    logs = get_recent_logs(15)
    if logs:
        now = datetime.now()
        for log in logs:
            p, roll, res, time_str = log
            
            # Calculate age of the log
            try:
                log_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                age = (now - log_time).total_seconds()
            except:
                age = 999
            
            # Calculate highlight opacity (fade out over 10 seconds)
            if age < 10:
                opacity = 0.4 * (1 - age / 10)
                bg_style = f"background-color: rgba(144, 238, 144, {opacity:.2f});"
                border_class = "log-entry-highlighted"
            else:
                bg_style = ""
                border_class = ""
            
            # Parse the result string for squares
            if '(' in res:
                # Expected format: total (d1 + d2 + mod)
                total, dice_part = res.split('(', 1)
                total = total.strip()
                dice_part = dice_part.rstrip(')')
                # Split by + while keeping - as part of the number
                # Regex to split by + or - but keep the - with the following number
                parts = re.split(r'\s*\+\s*', dice_part)
                dice_html = ""
                for part in parts:
                    clean_part = part.strip()
                    if clean_part.startswith("MOD:"):
                        mod_val = clean_part.replace("MOD:", "")
                        dice_html += f'<span class="dice-square" style="border-color: #888; color: #aaa; font-size: 0.8em;">Mod: {mod_val}</span>'
                    else:
                        dice_html += f'<span class="dice-square">{clean_part}</span>'
            else:
                total = res
                dice_html = f'<span class="dice-square">{res}</span>'

            st.markdown(f"""
                <div class="log-entry {border_class}" style="{bg_style}">
                    <strong style="font-size: 1.1em;">{p}</strong> -> {dice_html}<br>
                    <strong style="font-size: 1.2em;">Resultado</strong> -> <span style="font-size: 1.4em; font-weight: bold; color: #4CAF50;">{total}</span><br>
                    <small style='color:grey; font-size: 0.8em;'>{time_str} | {roll}</small>
                </div>
            """, unsafe_allow_html=True)
            st.divider()

st.sidebar.info("Rolagem de Dados")
