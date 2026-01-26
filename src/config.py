
import sys
print(sys.executable)

import os #um auf umgebungsvariablen zugreifen zu könenn
from pathlib import Path
from dotenv import load_dotenv # damit können  Variablen aus einer .env datei als umgebungsvariablen geholt werden.

# lädt .env aus Projektroot
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DB_UID = os.getenv("DB_UID")
DB_PWD = os.getenv("DB_PWD")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_COMMUNITY_ID = int(os.getenv("DB_COMMUNITY_ID", "12"))

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
