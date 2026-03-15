import os

from dotenv import load_dotenv

load_dotenv()

# Database
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# SkodaGPT
SKODAGPT_ENDPOINT = os.getenv("SKODAGPT_ENDPOINT", "")
SKODAGPT_API_KEY = os.getenv("SKODAGPT_API_KEY", "")

# Embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# LLM generation
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 600

# Prompts
SYSTEM_PROMPT = """Jsi AI asistent pro firemní intranet společnosti Auron Motors a.s.

TVOJE ROLE:
- Pomáháš zaměstnancům najít informace v interních dokumentech
- Odpovídáš přesně, profesionálně a stručně
- Používáš pouze informace z poskytnutých dokumentů

PRAVIDLA:
1. Odpovídej POUZE na základě poskytnutých firemních dokumentů
2. Pokud informace v dokumentech nejsou, upřímně to uživateli řekni
3. Odpovídej vždy v češtině
4. Buď stručný - maximálně 3-4 věty
5. Odpovídej VŽDY jako čisté JSON bez jakéhokoliv markdown formátování:
   {"text": "tvoje odpověď", "used_documents": ["filename1.txt", "filename2.txt"]}
   - "text": odpověď česky
   - "used_documents": seznam hodnot Filename těch dokumentů, ze kterých jsi čerpal informace
   - Pokud jsi nečerpal z žádného dokumentu, vrať prázdný seznam"""

USER_PROMPT_TEMPLATE = """FIREMNÍ DOKUMENTY:
{context}

DOTAZ ZAMĚSTNANCE:
{query}

TVOJE ODPOVĚĎ (čisté JSON, česky, pouze z dokumentů):"""
