import os
os.environ.setdefault('BN_UPDATER_SEED_VOTING_ADDRESS', '0x56741DbC203648983c359A48aaf68f25f5550B6a')
os.environ.setdefault('BN_UPDATER_SP_ADDRESS_MAINNET', '0x0aB346a16ceA1B1363b20430C414eAB7bC179324')
os.environ.setdefault('BN_UPDATER_SP_ADDRESS_IDCHAIN', '0x183C5D2d1E43A3aCC8a977023796996f8AFd2327')
os.environ.setdefault('BN_UPDATER_MAINNET_WSS', '')
os.environ.setdefault('BN_UPDATER_IDCHAIN_WSS', 'wss://idchain.one/ws/')
# Deliberately a hostname containing neither "rinkeby" nor "idchain" - an
# operator running their own node under their own domain (exactly the
# idchain-node-for-operators case #38 identified; #38's implementation,
# #46, fixes the sibling instance in consensus/receiver.py separately).
os.environ['BN_UPDATER_SEED_GROUPS_WS_URL'] = 'wss://my-own-node.example.com/ws/'
os.environ.setdefault('BN_CONSENSUS_IDCHAIN_RPC_URL', 'https://idchain.one/rpc/')
os.environ.setdefault('BN_ARANGO_PROTOCOL', 'http')
os.environ.setdefault('BN_ARANGO_HOST', 'localhost')
os.environ.setdefault('BN_ARANGO_PORT', '8529')

import unittest
from unittest.mock import patch, MagicMock

with patch('arango.ArangoClient', MagicMock()), patch('web3.Web3', MagicMock()):
    import seed_groups


class TestPoAMiddleware(unittest.TestCase):
    """
    seed_groups.py injected the PoA middleware only when the RPC URL's
    hostname happened to contain "rinkeby" or "idchain" - the same
    hostname-substring bug identified in consensus/receiver.py by #38
    (fixed there separately by #38's implementation, #46). A self-hosted
    PoA node under any other hostname silently got no PoA middleware,
    breaking header decoding on a Clique chain.
    """

    def test_injects_poa_middleware_regardless_of_hostname(self):
        seed_groups.w3.middleware_onion.inject.assert_called_once()


if __name__ == '__main__':
    unittest.main()
