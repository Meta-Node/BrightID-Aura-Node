import time
import base64
import requests
import traceback
from web3 import Web3
from arango import ArangoClient
from web3.middleware import geth_poa_middleware
from marshmallow import Schema, fields
import tools
import config

db = ArangoClient(hosts=config.ARANGO_SERVER).db('_system')
w3_mainnet = Web3(Web3.WebsocketProvider(
    config.MAINNET_WSS, websocket_kwargs={'timeout': 60}))
sp_contract_mainnet = w3_mainnet.eth.contract(
    address=config.MAINNET_SP_ADDRESS,
    abi=config.SP_ABI)

w3_idchain = Web3(Web3.WebsocketProvider(
    config.IDCHAIN_WSS, websocket_kwargs={'timeout': 60}))
w3_idchain.middleware_onion.inject(geth_poa_middleware, layer=0)
sp_contract_idchain = w3_idchain.eth.contract(
    address=config.IDCHAIN_SP_ADDRESS,
    abi=config.SP_ABI)

class AppSchema(Schema):
    _key = fields.String(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    context = fields.String(load_default='')
    verifications = fields.List(fields.String(), load_default=[])
    testing = fields.Boolean(required=True)
    idsAsHex = fields.Boolean(required=True)
    usingBlindSig = fields.Boolean(required=True)
    nodeUrl = fields.URL(load_default='', allow_none=True)
    verificationExpirationLength = fields.Integer(load_default=300000)
    soulbound = fields.Boolean(required=True)
    callbackUrl = fields.URL(load_default='', allow_none=True)
    url = fields.URL(load_default='', allow_none=True)
    logo = fields.String(load_default='')
    sponsoring = fields.Boolean(required=True)


app_schema = AppSchema()


def str2bytes32(s):
    assert len(s) <= 32
    padding = (2 * (32 - len(s))) * '0'
    return (bytes(s, 'utf-8')).hex() + padding


def get_logo(app_key, url):
    try:
        res = requests.get(url)
        file_format = url.split('.')[-1]
        if file_format == 'svg':
            file_format == 'svg+xml'
        logo = 'data:image/' + file_format + ';base64,' + \
            base64.b64encode(res.content).decode('ascii')
    except Exception as e:
        print(f'app: {app_key} => Error in getting logo: {e}')
        logo = ''
    return logo


def row_to_app(row):
    app = {
        '_key': row['key'],
        'name': row['name'],
        'sponsoring': row['sponsoring'],
        'testing': row['testing'],
        'idsAsHex': row['idsAsHex'],
        'soulbound': row['soulbound'],
        'usingBlindSig': row['usingBlindSig'],
        'verifications': row.get('verifications', []),
        'verificationExpirationLength': row.get('verificationExpirationLength'),
        'nodeUrl': row.get('nodeUrl'),
        'context': row.get('context'),
        'callbackUrl': row.get('callbackUrl'),
        'url': next(iter(row.get('links') or []), None),
        'logo': get_logo(row['key'], next(iter(row.get('images') or []), '')),
    }
    return app_schema.load({k: v for k, v in app.items() if v is not None})


def update():
    data = requests.get(config.APPS_JSON_FILE).json()

    cursor = db.aql.execute('''
        FOR s in sponsorships
            FILTER s.expireDate == null
            COLLECT app = s._to WITH COUNT INTO length
            RETURN {"app": PARSE_IDENTIFIER(app).key, "used": length}
    ''')
    used_sponsorships = {c['app']: c['used'] for c in cursor}

    for row in data:
        if not row.get('key'):
            app_name = row.get('name', 'Unknown App')
            print(f"Validation Error: App '{app_name}' is missing the required 'key' field.")
            continue

        try:
            app = row_to_app(row)
        except Exception as e:
            print(f'app: {row["key"]} => Invalid data: {e}')
            # try to update totalSponsorships
            app = {'_key': row['key']}

        try:
            app['totalSponsorships'] = get_sponsorships(app['_key'])
        except Exception as e:
            print(f'app: {row["key"]} => Error getting totalSponsorships: {e}')

        app['usedSponsorships'] = used_sponsorships.get(app['_key'], 0)

        db.aql.execute('''
            INSERT @app IN apps
            OPTIONS { overwriteMode: "update" }
        ''', bind_vars={
            'app': app
        })


def get_sponsorships(app_key):
    app_bytes = str2bytes32(app_key)
    mainnet_balance = sp_contract_mainnet.functions.totalContextBalance(
        app_bytes).call()
    idchain_balance = sp_contract_idchain.functions.totalContextBalance(
        app_bytes).call()
    totalSponsorships = mainnet_balance + idchain_balance
    return totalSponsorships


if __name__ == '__main__':
    try:
        print('\nUpdating apps', time.ctime())
        ts = time.time()
        update()

        bn = tools.get_idchain_block_number()
        db.aql.execute('''
            upsert { _key: "APPS_LAST_UPDATE" }
            insert { _key: "APPS_LAST_UPDATE", value: @bn }
            update { value: @bn }
            in variables
        ''', bind_vars={
            'bn': bn
        })

        print(f'Updating apps ended in {int(time.time() - ts)} seconds\n')
    except Exception as e:
        print(f'Error in apps updater: {e}\n')
        traceback.print_exc()
