import streamlit as st
from datetime import datetime
from database import add_dice_log, get_recent_logs
from streamlit_autorefresh import st_autorefresh
import random
import re

# --- Configuration ---
st.set_page_config(page_title="Sala de Rolagem", page_icon="🎲", layout="wide", initial_sidebar_state="expanded")

# --- CSS ---
st.markdown("""
    <style>
    .main { background-color: #1a1c24; color: #e0e0e0; }
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
    .log-entry {
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid transparent;
        transition: border-color 0.5s;
    }
    .log-entry-highlighted {
        border-left: 4px solid #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)

# --- Check for Name ---
if 'player_name_locked' not in st.session_state or not st.session_state.player_name_locked:
    st.warning("⚠️ Por favor, defina seu nome na página inicial antes de jogar.")
    st.stop()

player_name = st.session_state.player_name_locked

# --- Helpers ---
def parse_custom_roll(roll_str):
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
            op, val = op_part[0], int(op_part[1:])
            if op == '+': total += val; op_display = f" + {val}"
            elif op == '-': total -= val; op_display = f" - {val}"
            elif op == '*': total *= val; op_display = f" * {val}"
            elif op == '/' and val != 0: total //= val; op_display = f" / {val}"
        rolls_str = ' + '.join(map(str, rolls))
        return f"{total} ({rolls_str}){op_display}" if op_display else f"{total} ({rolls_str})"
    return None

# --- Global Toasts Logic ---
if 'last_seen_log_id' not in st.session_state:
    recent = get_recent_logs(1)
    st.session_state.last_seen_log_id = recent[0][0] if recent else 0

if 'toasts_queue' not in st.session_state:
    st.session_state.toasts_queue = {}

def check_for_new_rolls():
    import time
    now = time.time()
    recent_logs = get_recent_logs(10)
    if recent_logs:
        for log in reversed(recent_logs):
            log_id, p, roll, res, time_str = log
            if log_id > st.session_state.last_seen_log_id:
                if '(' in res:
                    total_val, details = res.split('(', 1)
                    details = details.rstrip(')')
                    msg = f"🎲 **{p}** rolou **{roll}**\n\nDados: `{details}`\n\nTotal: **{total_val.strip()}**"
                else:
                    msg = f"🎲 **{p}** rolou **{roll}**\n\nTotal: **{res}**"
                st.session_state.toasts_queue[log_id] = (msg, now)
                st.session_state.last_seen_log_id = log_id
    to_delete = []
    for lid, (msg, ts) in list(st.session_state.toasts_queue.items()):
        if now - ts < 15: st.toast(msg)
        else: to_delete.append(lid)
    for lid in to_delete: del st.session_state.toasts_queue[lid]

# --- Main Render ---
st_autorefresh(interval=3000, limit=None, key="dice_refresh")
check_for_new_rolls()

st.title("🎲 Sala de Rolagem")
st.info(f"🎭 Personagem: **{player_name}**")

c_roll, c_log = st.columns([1, 1])

with c_roll:
    st.write("### 🎲 Rolar Dados")
    with st.form("custom_roll_form", clear_on_submit=True):
        custom_roll = st.text_input("Comando de Rolagem (ex: 2d6+3, d20)", placeholder="Ex: 2d6+3")
        if st.form_submit_button("Lançar Dados"):
             if custom_roll:
                  result_details = parse_custom_roll(custom_roll)
                  if result_details:
                      add_dice_log(player_name, custom_roll, result_details)
                      st.rerun()
                  else: st.error("Formato inválido!")
             else: st.warning("Digite o comando.")

with c_log:
    st.write("### 📜 Histórico Global")
    logs = get_recent_logs(15)
    if logs:
        now = datetime.now()
        for log_id, p, roll, res, time_str in logs:
            try:
                log_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                age = (now - log_time).total_seconds()
                display_time = log_time.strftime("%d/%m/%Y %H:%M")
            except: age, display_time = 999, time_str
            
            bg_style = f"background-color: rgba(144, 238, 144, {0.4 * (1 - age / 10):.2f});" if age < 10 else ""
            border_class = "log-entry-highlighted" if age < 10 else ""
            
            if '(' in res:
                total_val, rest = res.split('(', 1)
                dice_part, op_part = rest.split(')', 1) if ')' in rest else (rest, "")
                dice_html = "".join([f'<span class="dice-square">{x.strip()}</span>' for x in re.split(r'\s*\+\s*', dice_part) if x.strip()])
                if op_part.strip(): dice_html += f' <span style="color: #888; font-weight: bold;">{op_part.strip()}</span>'
                total = total_val.strip()
            else: total, dice_html = res, f'<span class="dice-square">{res}</span>'

            st.markdown(f"""
                <div class="log-entry {border_class}" style="{bg_style}">
                    <strong style="font-size: 1.1em;">{p}</strong> jogou <code>{roll}</code> -> {dice_html}<br>
                    <strong style="font-size: 1.2em;">Resultado</strong> -> <span style="font-size: 1.4em; font-weight: bold; color: #4CAF50;">{total}</span><br>
                    <small style='color:grey; font-size: 0.8em;'>{display_time}</small>
                </div>
            """, unsafe_allow_html=True)
            st.divider()
