import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# runner imports config at module level, which reads these.
os.environ.setdefault('BN_ARANGO_PROTOCOL', 'http')
os.environ.setdefault('BN_ARANGO_HOST', 'localhost')
os.environ.setdefault('BN_ARANGO_PORT', '8529')
os.environ.setdefault('BN_CONSENSUS_SNAPSHOTS_PERIOD', '240')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The verifications package pulls in BrightID-AntiSybil, which is installed
# from a tarball in the scorer image and nowhere else. No verifier runs here,
# so a stub keeps this file runnable wherever python-arango is available.
sys.modules.setdefault('verifications', MagicMock())

with patch('arango.ArangoClient', MagicMock()):
    import runner


class TestRemovalBorder(unittest.TestCase):
    """
    process() writes this snapshot's verifications, then prunes everything
    below VERIFICATION_BLOCK. That read is the previous snapshot's block in
    normal operation, but a stale snapshot - one left in /snapshots across a
    database re-initialization, carrying a block number from the timeline the
    database no longer occupies - sets VERIFICATION_BLOCK *ahead* of the
    blocks that follow. The prune then deletes the rows just written.

    What that costs: seed_connected.last_verifications() reads the rows at
    VERIFICATION_BLOCK to carry seed-group quota counts forward, and finds
    nothing once they are gone, restarting every count at zero.

    What it does not fix: which block the API answers from. That is
    VERIFICATIONS_HASHES, whose highest key wins in both
    update_verifications_hashes() here and userVerifications() in
    web_services/foxx/v6/db.js - so a stale block stays the highest key and
    keeps being served whether or not this prune is capped.
    """

    def setUp(self):
        self.patches = [
            patch.object(runner, 'update_verifications_hashes'),
            patch.object(runner, 'verifiers', {}),
            patch.object(runner.shutil, 'rmtree'),
            patch.object(runner.os, 'system', return_value=0),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_border_does_not_pass_the_block_being_processed(self):
        runner.variables.get.return_value = {'value': 1100}
        with patch.object(runner, 'remove_verifications_before') as remove:
            runner.process('dump_920_fnl')
        remove.assert_called_once_with(920)

    def test_border_is_the_previous_block_in_normal_operation(self):
        runner.variables.get.return_value = {'value': 680}
        with patch.object(runner, 'remove_verifications_before') as remove:
            runner.process('dump_920_fnl')
        remove.assert_called_once_with(680)


if __name__ == '__main__':
    unittest.main()
