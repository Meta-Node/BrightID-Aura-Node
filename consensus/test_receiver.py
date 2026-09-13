import os
import subprocess
import sys
import textwrap
import unittest

_CHILD_ENV = {
    'BN_CONSENSUS_INFURA_URL': 'wss://idchain.one/ws/',
    'BN_CONSENSUS_MAX_DATA_SIZE': '100000',
    'BN_CONSENSUS_GAS': '2000000',
    'BN_CONSENSUS_GAS_PRICE': '10000000000',
    'BN_CONSENSUS_TO_ADDRESS': '0xb1d1CDd5C4C541f95A73b5748392A6990cBe32b7',
    'BN_CONSENSUS_SNAPSHOTS_PERIOD': '240',
    'BN_ARANGO_PROTOCOL': 'http',
    'BN_ARANGO_HOST': 'localhost',
    'BN_ARANGO_PORT': '8529',
    'BN_CONSENSUS_APPLY_URL': '/_db/_system/apply{v}/operations/{hash}',
    'BN_CONSENSUS_DUMP_URL': '/_api/replication/dump',
    'BN_CONSENSUS_IDCHAIN_RPC_URL': 'https://idchain.one/rpc/',
}

# Runs in a throwaway child process, never in the test runner itself: on the
# unpatched code this recurses until the interpreter hits a native C-stack
# overflow and segfaults (the production incident - exit 139, invisible to
# any Python-level try/except), which must not be allowed to take the test
# process down with it.
_CHILD_SCRIPT = textwrap.dedent('''
    from unittest.mock import patch, MagicMock
    with patch('arango.ArangoClient', MagicMock()), patch('web3.Web3', MagicMock()):
        import receiver
    with patch.object(receiver, 'requests') as mock_requests:
        mock_requests.post.side_effect = Exception('rpc unreachable')
        receiver.update_num_sealers()
        assert mock_requests.post.call_count == 1, (
            f'expected exactly one attempt, got {mock_requests.post.call_count}'
        )
    print('DONE')
''')


class TestUpdateNumSealers(unittest.TestCase):
    """
    Production incident: a transient RPC error during an IDChain reorg made
    update_num_sealers retry itself with no delay and no depth bound, ~1,347
    frames deep, segfaulting the interpreter (exit 139) - invisible to any
    Python-level try/except, and with no restart policy the node stayed
    down for 9 hours. The repro runs in a child process so a real crash
    here can't take this test run down with it.
    """

    def test_does_not_crash_or_recurse_on_repeated_failure(self):
        env = dict(os.environ)
        env.update(_CHILD_ENV)
        result = subprocess.run(
            [sys.executable, '-c', _CHILD_SCRIPT],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode < 0:
            self.fail(
                f'child process was killed by signal {-result.returncode} '
                f'(a native crash, not a Python exception) - '
                f'stderr tail:\\n{result.stderr[-2000:]}'
            )
        self.assertEqual(
            result.returncode, 0,
            f'child process exited {result.returncode}, stderr:\\n{result.stderr[-2000:]}'
        )
        self.assertIn('DONE', result.stdout)


if __name__ == '__main__':
    unittest.main()
