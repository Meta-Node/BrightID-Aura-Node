import os
os.environ.setdefault('BN_UPDATER_SEED_VOTING_ADDRESS', '0x56741DbC203648983c359A48aaf68f25f5550B6a')
os.environ.setdefault('BN_UPDATER_SP_ADDRESS_MAINNET', '0x0aB346a16ceA1B1363b20430C414eAB7bC179324')
os.environ.setdefault('BN_UPDATER_SP_ADDRESS_IDCHAIN', '0x183C5D2d1E43A3aCC8a977023796996f8AFd2327')
os.environ.setdefault('BN_UPDATER_MAINNET_WSS', '')
os.environ.setdefault('BN_UPDATER_IDCHAIN_WSS', 'wss://idchain.one/ws/')
os.environ.setdefault('BN_UPDATER_SEED_GROUPS_WS_URL', 'wss://idchain.one/ws/')
os.environ.setdefault('BN_ARANGO_PROTOCOL', 'http')
os.environ.setdefault('BN_ARANGO_HOST', 'localhost')
os.environ.setdefault('BN_ARANGO_PORT', '8529')

import io
import contextlib
import unittest
from unittest.mock import patch, MagicMock

import requests

# apps.py connects to ArangoDB and two web3 providers at import time.
# Patching arango.ArangoClient and web3.Web3 during the import keeps these
# tests from opening any socket.
with patch('arango.ArangoClient', MagicMock()), patch('web3.Web3', MagicMock()):
    import apps


def response(status, body):
    res = MagicMock()
    res.status_code = status
    if isinstance(body, Exception):
        res.json.side_effect = body
    else:
        res.json.return_value = body
    return res


APP_ROW = {
    'key': 'testapp',
    'name': 'Test App',
    'sponsoring': True,
    'testing': False,
    'idsAsHex': True,
    'soulbound': False,
    'usingBlindSig': False,
}


class TestAppsUpdate(unittest.TestCase):
    """
    A failed fetch (request error, non-2xx status, or a body that is not a
    list) must be logged and must leave APPS_LAST_UPDATE, the record of the
    last apps refresh, unchanged. Only a successful refresh advances it.
    Without the status and list checks, update() would iterate the API's
    JSON error object as if it were the apps list, and crash.
    """

    def setUp(self):
        apps.db.reset_mock()
        apps.db.aql.execute.side_effect = None
        apps.db.aql.execute.return_value = []
        patches = [
            patch.object(apps.tools, 'get_idchain_block_number', return_value=123),
            patch.object(apps, 'get_sponsorships', return_value=0),
            patch.object(apps, 'get_logo', return_value=''),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def run_main(self, get):
        out = io.StringIO()
        with patch.object(apps.requests, 'get', get), \
                contextlib.redirect_stdout(out):
            apps.main()
        return out.getvalue()

    def queries(self):
        return [c[0][0] for c in apps.db.aql.execute.call_args_list]

    def last_update_written(self):
        return any('APPS_LAST_UPDATE' in q for q in self.queries())

    def test_http_error_with_json_body(self):
        body = {'error': 'Your account or project has exceeded the quota'}
        out = self.run_main(MagicMock(return_value=response(500, body)))
        self.assertFalse(self.last_update_written())
        self.assertEqual(self.queries(), [])
        self.assertIn('HTTP 500: Your account or project has exceeded the quota', out)
        self.assertNotIn('Traceback', out)

    def test_http_error_message_field(self):
        out = self.run_main(MagicMock(
            return_value=response(503, {'message': 'down for maintenance'})))
        self.assertFalse(self.last_update_written())
        self.assertIn('HTTP 503: down for maintenance', out)

    def test_http_error_without_json_body(self):
        out = self.run_main(MagicMock(
            return_value=response(502, ValueError('not json'))))
        self.assertFalse(self.last_update_written())
        self.assertIn('HTTP 502', out)

    def test_non_list_body(self):
        out = self.run_main(MagicMock(
            return_value=response(200, {'apps': [APP_ROW]})))
        self.assertFalse(self.last_update_written())
        self.assertEqual(self.queries(), [])
        self.assertIn('expected a JSON list, got dict', out)

    def test_request_exception(self):
        out = self.run_main(MagicMock(
            side_effect=requests.exceptions.ConnectionError('DNS failure')))
        self.assertFalse(self.last_update_written())
        self.assertIn('request failed: DNS failure', out)
        self.assertNotIn('Traceback', out)

    def test_successful_list(self):
        self.run_main(MagicMock(return_value=response(200, [APP_ROW])))
        self.assertTrue(self.last_update_written())
        inserts = [c for c in apps.db.aql.execute.call_args_list
                   if 'INSERT @app IN apps' in c[0][0]]
        self.assertEqual(len(inserts), 1)
        self.assertEqual(inserts[0][1]['bind_vars']['app']['_key'], 'testapp')

    def test_update_returns_false_without_raising_on_failed_fetch(self):
        # start.py calls apps.update() before updating seed groups and
        # sponsorships. If update() raised, those two updates would not run.
        with patch.object(apps.requests, 'get',
                          MagicMock(return_value=response(500, {'error': 'x'}))), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(apps.update())


if __name__ == '__main__':
    unittest.main()
