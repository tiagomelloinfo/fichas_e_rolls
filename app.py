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
    # Regex for standard dice notation: [num]d[sides][op][val]
    # op can be +, -, * or /
    pattern = r'^(\d+)?d(\d+)([\+\-\*\/]\d+)?$'
    clean_str = roll_str.replace(" ", "").lower()
    match = re.match(pattern, clean_str)
    
    if match:
        num = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        op_part = match.group(3)
        
        rolls = [random.randint(1, sides) for _ in range(num)]
        sum_rolls = sum(rolls)
        
        total = sum_rolls
        op_display = ""
        
        if op_part:
            op = op_part[0]
            val = int(op_part[1:])
            if op == '+':
                total += val
                op_display = f" + {val}"
            elif op == '-':
                total -= val
                op_display = f" - {val}"
            elif op == '*':
                total *= val
                op_display = f" * {val}"
            elif op == '/':
                if val != 0:
                    total //= val
                    op_display = f" / {val}"
        
        # Detail string for the log
        rolls_str = ' + '.join(map(str, rolls))
        if op_display:
            details = f"{total} ({rolls_str}){op_display}"
        else:
            details = f"{total} ({rolls_str})"
        return details
    return None

# --- Initialization ---
init_db()

if 'last_seen_log_id' not in st.session_state:
    recent = get_recent_logs(1)
    st.session_state.last_seen_log_id = recent[0][0] if recent else 0

# --- App Title ---
st.title("🎲 Rolagem de Dados")

# --- Sidebar Configuration ---
st.sidebar.info("Rolagem de Dados")
st.sidebar.markdown("---")

# --- ROLAGEM DE DADOS ---
# Auto-refresh every 3 seconds to keep history updated and match animation
st_autorefresh(interval=3000, limit=None, key="dice_refresh")

st.subheader("🎲 Sala de Rolagem")

# Player Name Input with locking mechanism
if 'player_name_locked' not in st.session_state:
    st.session_state.player_name_locked = ""

if not st.session_state.player_name_locked:
    temp_name = st.text_input("Seu Nome de Personagem / Jogador", value="", placeholder="Digite seu nome e aperte Enter para travar...")
    if temp_name:
        st.session_state.player_name_locked = temp_name.strip().title()
        st.rerun()
    player_name = ""
    st.warning("⚠️ Você precisa definir seu nome para começar a jogar.")
else:
    st.info(f"🎭 Jogando como: **{st.session_state.player_name_locked}**")
    player_name = st.session_state.player_name_locked

st.divider()

c_roll, c_log = st.columns([1, 1])

with c_roll:
    st.write("### 🎲 Rolar Dados")
    
    with st.form("custom_roll_form", clear_on_submit=True):
        custom_roll = st.text_input("Comando de Rolagem (ex: 2d6+3, d20, 1d100)", placeholder="Ex: 2d6+3")
        if st.form_submit_button("Lançar Dados", disabled=not player_name):
             if custom_roll:
                  result_details = parse_custom_roll(custom_roll)
                  if result_details:
                      add_dice_log(player_name, custom_roll, result_details)
                      st.rerun()
                  else:
                      st.error("Formato inválido! Use algo como 2d6, 1d20+5 ou d10-1.")
             else:
                  st.warning("Digite o comando dos dados.")

with c_log:
    st.write("### 📜 Histórico Global")
    
    logs = get_recent_logs(15)
    if logs:
        now = datetime.now()
        for log in logs:
            log_id, p, roll, res, time_str = log
            
            # Calculate age of the log
            try:
                log_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                age = (now - log_time).total_seconds()
                display_time = log_time.strftime("%d/%m/%Y %H:%M")
            except:
                age = 999
                display_time = time_str
            
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
                # Format: total (d1 + d2 + ...) operator val
                total_val, rest = res.split('(', 1)
                total_val = total_val.strip()
                
                # Split at the closing parenthesis
                if ')' in rest:
                    dice_part, op_part = rest.split(')', 1)
                else:
                    dice_part, op_part = rest, ""
                
                # Render dice as squares
                dice_parts = re.split(r'\s*\+\s*', dice_part)
                dice_html = ""
                for part in dice_parts:
                    clean_part = part.strip()
                    if clean_part:
                        dice_html += f'<span class="dice-square">{clean_part}</span>'
                
                # Append operator if exists
                if op_part.strip():
                    dice_html += f' <span style="color: #888; font-weight: bold;">{op_part.strip()}</span>'
                
                total = total_val
            else:
                total = res
                dice_html = f'<span class="dice-square">{res}</span>'

            st.markdown(f"""
                <div class="log-entry {border_class}" style="{bg_style}">
                    <strong style="font-size: 1.1em;">{p}</strong> jogou <code>{roll}</code> -> {dice_html}<br>
                    <strong style="font-size: 1.2em;">Resultado</strong> -> <span style="font-size: 1.4em; font-weight: bold; color: #4CAF50;">{total}</span><br>
                    <small style='color:grey; font-size: 0.8em;'>{display_time}</small>
                </div>
            """, unsafe_allow_html=True)
            st.divider()

st.sidebar.info("Rolagem de Dados")

# --- Global Toasts Logic (Persistent for 15s) ---
if 'toasts_queue' not in st.session_state:
    st.session_state.toasts_queue = {} # {log_id: (msg, timestamp)}

def check_for_new_rolls():
    import time
    now = time.time()
    
    # 1. Check for new rolls in DB
    recent_logs = get_recent_logs(10)
    if recent_logs:
        for log in reversed(recent_logs):
            log_id, p, roll, res, time_str = log
            if log_id > st.session_state.last_seen_log_id:
                # Parse "total (d1 + d2 + ...)"
                if '(' in res:
                    total_val, details = res.split('(', 1)
                    total_val = total_val.strip()
                    details = details.rstrip(')')
                    msg = f"🎲 **{p}** rolou **{roll}**\n\nDados: `{details}`\n\nTotal: **{total_val}**"
                else:
                    msg = f"🎲 **{p}** rolou **{roll}**\n\nTotal: **{res}**"
                
                st.session_state.toasts_queue[log_id] = (msg, now)
                st.session_state.last_seen_log_id = log_id
    
    # 2. Display all active toasts and cleanup
    to_delete = []
    for lid, (msg, ts) in list(st.session_state.toasts_queue.items()):
        if now - ts < 15:
            st.toast(msg)
        else:
            to_delete.append(lid)
    
    for lid in to_delete:
        del st.session_state.toasts_queue[lid]

check_for_new_rolls()
