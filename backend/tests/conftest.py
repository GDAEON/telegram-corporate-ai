import os
import sys
import types
import sqlalchemy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_DIR = os.path.join(ROOT, 'backend')
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Stub logging_loki so logging_setup does not require external dependency
fake_logging_loki = types.ModuleType('logging_loki')
class DummyLokiHandler:
    def __init__(self, *a, **k):
        pass
fake_logging_loki.LokiHandler = DummyLokiHandler
sys.modules.setdefault('logging_loki', fake_logging_loki)

os.environ.setdefault('FERNET_KEY', 'QFPVedhtX4KhsMWj5ONkL8pjJi0FserBtEDwGDIIDS8=')
os.environ.setdefault('POSTGRES_URL', 'localhost')
os.environ.setdefault('POSTGRES_USER', 'user')
os.environ.setdefault('POSTGRES_PASSWORD', 'pass')
os.environ.setdefault('POSTGRES_DB', 'db')
os.environ.setdefault('REDIS_URL', 'localhost')
os.environ.setdefault('REDIS_PASSWORD', 'pass')
os.environ.setdefault('PROMETHEUS_JOBS_PATH', '/tmp/jobs.json')

_real_create_engine = sqlalchemy.create_engine

def _sqlite_engine(*args, **kwargs):
    return _real_create_engine('sqlite:///:memory:')

sqlalchemy.create_engine = _sqlite_engine
