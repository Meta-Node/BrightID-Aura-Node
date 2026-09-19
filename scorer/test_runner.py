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
    below VERIFICATION_BLOCK. In normal operation that read is the previous
    snapshot's block, so the prune leaves the rows just written alone.

    It does not when the snapshot being processed is numbered BELOW
    VERIFICATION_BLOCK, which happens after a re-initialization restores a
    backup older than snapshots still sitting in /snapshots. The border then
    runs past the block just processed and deletes its rows.
    seed_connected.last_verifications() reads those rows to carry seed-group
    quota counts forward and restarts every count at zero without them.

    That state resolves itself once the receiver re-reaches the higher block
    number, so this is an invariant rather than a fix for a live hazard: the
    prune border never exceeds the block just processed.
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
