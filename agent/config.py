import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly target backend/.env so this module works regardless of CWD
# (uvicorn from backend/, tests from repo root, Docker from /app — all the same path)
_dotenv_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=_dotenv_path)

# Project Paths
ROOT_DIR = Path(__file__).resolve().parent.parent

# ArmorIQ Configuration
raw_key = os.environ.get("ARMORIQ_API_KEY", "placeholder-api-key")
if not (raw_key.startswith("ak_live_") or raw_key.startswith("ak_claw_") or raw_key.startswith("ak_test_")):
    ARMORIQ_API_KEY = f"ak_test_{raw_key}"
else:
    ARMORIQ_API_KEY = raw_key

ARMORIQ_AGENT_ID = os.environ.get("ARMORIQ_AGENT_ID", "placeholder-agent-id")

# LLM Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

# Binary Paths
NMAP_PATH = os.environ.get("NMAP_PATH", "nmap")
NUCLEI_PATH = os.environ.get("NUCLEI_PATH", "nuclei")

# Default path for local ProjectDiscovery httpx binary
DEFAULT_HTTPX_PATH = "C:\\Users\\LENOVO\\Downloads\\httpx_1.9.0_windows_amd64\\httpx.exe"
if not Path(DEFAULT_HTTPX_PATH).exists():
    DEFAULT_HTTPX_PATH = "httpx"  # Fallback to PATH
HTTPX_PATH = os.environ.get("HTTPX_PATH", DEFAULT_HTTPX_PATH)

# Path to sqlmap.py script
DEFAULT_SQLMAP_PATH = str(ROOT_DIR / "sqlmap" / "sqlmap.py")
SQLMAP_PATH = os.environ.get("SQLMAP_PATH", DEFAULT_SQLMAP_PATH)
