"""Per-process benchmark state. Never edit shared auth/config or copy refresh tokens."""
from contextlib import contextmanager
import base64
import json
import math
import os
from pathlib import Path
import tempfile
import time
from datetime import datetime, timezone


def access_token(source_home, minimum_lifetime=1800):
    # Read only. Do not include credential values in exceptions or telemetry.
    try:
        auth = json.loads((Path(source_home) / 'auth.json').read_text())
        if auth.get('auth_mode') != 'chatgpt':
            raise ValueError('unsupported session mode')
        token = auth['tokens']['access_token']
        part = token.split('.')[1]
        payload = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
        expiry = payload['exp']
        if (isinstance(expiry, bool) or not isinstance(expiry, (int, float))
                or not math.isfinite(expiry) or expiry < time.time() + minimum_lifetime):
            raise ValueError('invalid or short-lived token')
    except (OSError, KeyError, ValueError, TypeError, IndexError, AttributeError, OverflowError):
        raise RuntimeError('No readable access token with sufficient remaining lifetime; shared login was not modified') from None
    return auth


@contextmanager
def isolated_home(source_home=None):
    source = Path(source_home or os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    auth = access_token(source)
    runtime_root = Path(__file__).resolve().parents[1] / '.lunarmarch' / 'isolated-runtime'
    runtime_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix='call-', dir=runtime_root) as temporary:
        home = Path(temporary)
        home.chmod(0o700)
        env = {k:v for k,v in os.environ.items() if not k.startswith('CODEX_') and k != 'OPENAI_API_KEY'}
        env.update(CODEX_HOME=str(home), CODEX_SQLITE_HOME=str(home / 'sqlite'))
        # The CLI access-token login accepts agent-identity credentials, not this
        # cached ChatGPT token format. Preserve only required session fields;
        # refresh credentials are deliberately absent from the private runtime.
        tokens = auth['tokens']
        local_auth = {'auth_mode': 'chatgpt', 'OPENAI_API_KEY': None,
                      'tokens': {key: tokens[key] for key in ('id_token', 'access_token', 'account_id') if key in tokens},
                      'last_refresh': datetime.now(timezone.utc).isoformat()}
        local_auth['tokens']['refresh_token'] = ''
        credential = home / 'auth.json'
        descriptor = os.open(credential, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(local_auth, stream)
        yield env
