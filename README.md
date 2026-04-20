# 🐉 Old Dragon 2 - Gerenciador de Fichas e Rolagens

Este projeto é um sistema simples e elegante para mestres e jogadores de **Old Dragon 2** gerenciarem suas fichas de personagem e realizarem rolagens de dados compartilhadas em tempo real.

## 🚀 Funcionalidades

- **Gerenciamento de Fichas**: Crie, edite e remova fichas de personagem.
- **Automação OD2**:
    - Cálculo automático de modificadores de atributos (3-20).
    - Cálculo automático de Jogadas de Proteção (Física, Mental e Esquiva) baseado no nível e atributos.
- **Sala de Dados Compartilhada**:
    - Role dados padrão (d4, d6, d8, d10, d12, d20, d100).
    - Suporte para rolagens customizadas (ex: `2d6+4`).
    - Histórico de rolagens global que aparece para todos os jogadores.
- **Interface Premium**: Design escuro otimizado para sessões de RPG.

## 🛠️ Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) - Interface web.
- [SQLite](https://sqlite.org/) - Banco de dados local para persistência.
- [Python](https://www.python.org/) - Lógica do sistema.

## 📦 Como Instalar e Rodar

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/tiagomelloinfo/fichas_e_rolls.git
   cd fichas_e_rolls
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o sistema:**
   ```bash
   streamlit run app.py
   ```

---
Desenvolvido para facilitar suas aventuras no Velho Mundo! ⚔️🛡️
