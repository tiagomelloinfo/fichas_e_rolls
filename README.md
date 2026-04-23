# 🐉 RPG Manager - Rolagens e Mapa Tático

Este projeto é um sistema simples e elegante para mestres e jogadores de RPG gerenciarem suas sessões com rolagens de dados compartilhadas e um mapa tático interativo em tempo real.

## 🚀 Funcionalidades

- **Lobby de Entrada**: Identificação de personagem com travamento de nome (imutável após a entrada) e formatação automática (.title()).
- **Sala de Rolagem Global**:
    - Suporte para rolagens complexas com operadores matemáticos (`2d6+4`, `3d10*5`, `10d4/2`).
    - Histórico global sincronizado em tempo real.
    - Notificações (toasts) que aparecem para todos os jogadores quando alguém rola um dado, com persistência de 15 segundos.
    - Exibição visual detalhada com dados individuais em destaque.
- **Mapa Tático Interativo**:
    - Grid de combate denso (32x32).
    - Suporte para upload de mapas locais (JPG/PNG) pelo Mestre.
    - Posicionamento de personagens e monstros com cores diferenciadas.
    - Sincronização em tempo real entre todos os jogadores.
- **Interface Premium**: Design escuro otimizado para sessões de RPG, com animações e destaques.
- **Fuso Horário Local**: Registros de jogadas configurados para o horário de Brasília (UTC-3).

## 🛠️ Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) - Interface web e sistema multi-páginas.
- [SQLite](https://sqlite.org/) - Banco de dados local para persistência de rolagens e estado do mapa.
- [Python 3.12+](https://www.python.org/) - Lógica do sistema.

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
