import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # en APK no existe dotenv

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
