import sqlite3
from datetime import datetime

DB_NAME = 'old_dragon_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Characters table
    c.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            race TEXT,
            char_class TEXT,
            level INTEGER DEFAULT 1,
            alignment TEXT,
            xp INTEGER DEFAULT 0,
            str_val INTEGER,
            dex_val INTEGER,
            con_val INTEGER,
            int_val INTEGER,
            wis_val INTEGER,
            cha_val INTEGER,
            hp_max INTEGER,
            hp_current INTEGER,
            ac INTEGER,
            ba INTEGER,
            jp_physical INTEGER,
            jp_mental INTEGER,
            jp_evasion INTEGER,
            inventory TEXT,
            gold_po INTEGER DEFAULT 0,
            gold_pp INTEGER DEFAULT 0,
            gold_pc INTEGER DEFAULT 0,
            notes TEXT
        )
    ''')
    # Dice logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS dice_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            roll_type TEXT,
            result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- Character Functions ---
def add_character(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    keys = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    query = f"INSERT INTO characters ({keys}) VALUES ({placeholders})"
    c.execute(query, list(data.values()))
    conn.commit()
    conn.close()

def get_all_characters():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, char_class, level FROM characters")
    data = c.fetchall()
    conn.close()
    return data

def get_character_by_id(char_id):
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM characters WHERE id=?", (char_id,))
    data = c.fetchone()
    conn.close()
    return dict(data) if data else None

def update_character(char_id, data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    settings = ', '.join([f"{k} = ?" for k in data.keys()])
    values = list(data.values())
    values.append(char_id)
    query = f"UPDATE characters SET {settings} WHERE id = ?"
    c.execute(query, values)
    conn.commit()
    conn.close()

def delete_character(char_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM characters WHERE id=?", (char_id,))
    conn.commit()
    conn.close()

# --- Dice Log Functions ---
def add_dice_log(player, roll, result):
    from datetime import timedelta, timezone
    # Brazil/Sao Paulo is UTC-3 (currently no DST in Brazil)
    br_tz = timezone(timedelta(hours=-3))
    now_br = datetime.now(br_tz)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO dice_logs (player_name, roll_type, result, timestamp) VALUES (?, ?, ?, ?)",
              (player, roll, result, now_br.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_recent_logs(limit=20):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, player_name, roll_type, result, timestamp FROM dice_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    data = c.fetchall()
    conn.close()
    return data
