import os
import shutil

SNAPSHOTS_PATH = "/snapshots"
# INIT_BRIGHTID_DB is baked into the container when it is created, so every
# later start would clear /snapshots again. The marker records that this
# container has already done it, and lives outside the snapshots volume so
# that recreating the container arms it once more.
INIT_MARKER = "/var/local/brightid-snapshots-cleared"

if os.environ.get('INIT_BRIGHTID_DB') == '1' and not os.path.exists(INIT_MARKER):
    for fname in os.listdir(SNAPSHOTS_PATH):
        fpath = os.path.join(SNAPSHOTS_PATH, fname)
        if os.path.isfile(fpath) or os.path.islink(fpath):
            os.unlink(fpath)
        elif os.path.isdir(fpath):
            shutil.rmtree(fpath)
    os.makedirs(os.path.dirname(INIT_MARKER), exist_ok=True)
    open(INIT_MARKER, 'w').close()

BN_ARANGO_PROTOCOL = os.environ['BN_ARANGO_PROTOCOL']
BN_ARANGO_HOST = os.environ['BN_ARANGO_HOST']
BN_ARANGO_PORT = int(os.environ['BN_ARANGO_PORT'])
ARANGO_SERVER = f'{BN_ARANGO_PROTOCOL}://{BN_ARANGO_HOST}:{BN_ARANGO_PORT}'
SNAPSHOTS_PERIOD = int(os.environ['BN_CONSENSUS_SNAPSHOTS_PERIOD'])
if 'AURA_SNAPSHOT_DIR' in os.environ:
    AURA_SNAPSHOT_DIR = os.environ['AURA_SNAPSHOT_DIR']
else:
    AURA_SNAPSHOT_DIR = f'/tmp/aura'

