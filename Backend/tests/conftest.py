import os
import pathlib
import sys

# Base de datos propia para los tests, siempre limpia
RUTA_DB = pathlib.Path(__file__).parent / "test_academia.db"
if RUTA_DB.exists():
    RUTA_DB.unlink()

os.environ['DATABASE_URL'] = f"sqlite:///{RUTA_DB}"
os.environ['ADMIN_EMAIL'] = 'admin@test.com'
os.environ['RATELIMIT_ENABLED'] = '0'
os.environ.pop('STRIPE_SECRET_KEY', None)
os.environ.pop('STRIPE_WEBHOOK_SECRET', None)

# Para poder hacer 'import main' desde los tests
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
