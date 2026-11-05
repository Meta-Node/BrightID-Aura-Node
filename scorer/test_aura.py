import contextlib
import copy
import importlib.util
import io
import os
from pathlib import Path
import types
import unittest
from unittest.mock import patch
import uuid

from arango import ArangoClient


@unittest.skipUnless(os.environ.get('AURA_TEST_ARANGO_URL'),
                     'set AURA_TEST_ARANGO_URL to a disposable ArangoDB server')
class AuraDomainIsolationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        endpoint = os.environ['AURA_TEST_ARANGO_URL']
        cls.admin = ArangoClient(hosts=endpoint).db('_system')
        config = types.SimpleNamespace(
            ARANGO_SERVER=endpoint, BN_ARANGO_HOST='unused',
            BN_ARANGO_PORT=8529, AURA_SNAPSHOT_DIR='/unused',
        )
        spec = importlib.util.spec_from_file_location(
            'aura_under_test', Path(__file__).parent / 'verifications' / 'aura.py',
        )
        cls.aura = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', {'config': config}):
            spec.loader.exec_module(cls.aura)

    def setUp(self):
        name = 'aura_test_' + uuid.uuid4().hex
        self.admin.create_database(name)
        self.addCleanup(self.admin.delete_database, name)
        self.db = ArangoClient(hosts=os.environ['AURA_TEST_ARANGO_URL']).db(name)
        self.connections = self.db.create_collection('connections', edge=True)
        self.db.create_collection('verifications')
        for source, target, category in (
            ('owner', 'owner', 'manager'), ('owner', 'trainer', 'trainer'),
            ('trainer', 'player', 'player'), ('player', 'subject', 'subject'),
        ):
            self.connections.insert({
                '_key': category, '_from': 'users/' + source,
                '_to': 'users/' + target,
                'auraEvaluations': [{
                    'domain': 'BrightID', 'category': category,
                    'evaluation': 'positive', 'confidence': 4, 'modified': 123,
                }],
            })

    def score(self):
        self.db.collection('verifications').truncate()
        with patch.object(self.aura, 'snapshot', self.db), \
                patch.object(self.aura, 'system', self.db), \
                patch.object(self.aura, 'TEAM_OWNERS', ['owner']), \
                patch.object(self.aura.os, 'system', return_value=0), \
                contextlib.redirect_stdout(io.StringIO()):
            self.aura.verify(42)
        return {
            'aura': list(self.db.aql.execute(
                'FOR a IN aura SORT a._key RETURN UNSET(a, "_id", "_rev")')),
            'energy': list(self.db.aql.execute(
                'FOR e IN energy SORT e._key RETURN {id: e._key, energy: e.energy}')),
            'verifications': list(self.db.aql.execute(
                'FOR v IN verifications SORT v.user '
                'RETURN KEEP(v, "name", "user", "block", "domains")')),
        }

    def test_brightid_only_scores_levels_and_impacts(self):
        result = self.score()
        expected = {
            'manager': (4000000, 2), 'trainer': (16000000, 2),
            'player': (64000000, 3), 'subject': (256000000, 4),
        }
        self.assertEqual(len(result['aura']), 4)
        self.assertEqual(len(result['verifications']), 4)
        self.assertEqual(result['energy'], [{'id': 'owner', 'energy': 1000000}])
        for record in result['aura']:
            self.assertEqual(len(record['domains']), 1)
            domain = record['domains'][0]
            self.assertEqual(domain['name'], 'BrightID')
            self.assertEqual(len(domain['categories']), 1)
            category = domain['categories'][0]
            score, level = expected[category['name']]
            self.assertEqual((category['score'], category['level']), (score, level))
            self.assertEqual(len(category['impacts']), 1)
            self.assertEqual(category['impacts'][0]['impact'], score)
            self.assertEqual(category['impacts'][0]['confidence'], 4)
            self.assertEqual(category['impacts'][0]['modified'], 123)

    def test_matching_roles_in_other_domains_do_not_change_brightid(self):
        baseline = self.score()
        originals = list(self.connections.all())
        for domain in ('Interfold', 'interfold', 'brightid', '', None, 'missing'):
            for answer in ('positive', 'negative'):
                with self.subTest(domain=domain, answer=answer):
                    for original in originals:
                        connection = copy.deepcopy(original)
                        other = dict(connection['auraEvaluations'][0],
                                     domain=domain, evaluation=answer, confidence=3)
                        if domain == 'missing':
                            del other['domain']
                        connection['auraEvaluations'].append(other)
                        self.connections.replace(connection, check_rev=False)
                    self.assertEqual(self.score(), baseline)

    def test_other_domain_manager_changes_cannot_redirect_energy(self):
        baseline = self.score()
        for answer, confidence in (('positive', 1), ('positive', 4), ('negative', 4)):
            with self.subTest(answer=answer, confidence=confidence):
                self.connections.insert({
                    '_key': 'outside', '_from': 'users/owner', '_to': 'users/outsider',
                    'auraEvaluations': [{
                        'domain': 'Interfold', 'category': 'manager',
                        'evaluation': answer, 'confidence': confidence, 'modified': 456,
                    }],
                }, overwrite=True)
                self.assertEqual(self.score(), baseline)

    def test_replaced_other_domain_manager_cannot_redirect_energy(self):
        baseline = self.score()
        manager = self.connections.get('manager')
        brightid = manager['auraEvaluations'][0]
        for answer, confidence in (('positive', 4), ('negative', 1), ('positive', 1)):
            with self.subTest(answer=answer, confidence=confidence):
                # The node's evaluate() in web_services/foxx/v6/db.js keeps one
                # evaluation per domain and category on an edge. A second
                # Interfold manager write on this edge replaces the first
                # Interfold one, and the BrightID manager evaluation from
                # setUp stays. So each subTest gives the edge exactly those two
                # evaluations, and the BrightID scores must not move.
                manager['auraEvaluations'] = [brightid, {
                    'domain': 'Interfold', 'category': 'manager',
                    'evaluation': answer, 'confidence': confidence, 'modified': 789,
                }]
                self.connections.replace(manager, check_rev=False)
                self.assertEqual(self.score(), baseline)

    def test_other_domain_roles_produce_no_brightid_verifications(self):
        for connection in self.connections.all():
            connection['auraEvaluations'][0]['domain'] = 'Interfold'
            self.connections.replace(connection)
        self.assertEqual(self.score(), {'aura': [], 'energy': [], 'verifications': []})

    def test_interfold_answers_remain_stored_without_scoring(self):
        baseline = self.score()
        self.connections.insert({
            '_key': 'answers', '_from': 'users/owner', '_to': 'users/operator',
            'auraEvaluations': [{
                'domain': 'Interfold', 'category': category,
                'evaluation': 'positive', 'confidence': 4, 'modified': 123,
            } for category in ('Keyholder', 'Self-custody', 'Disclosure')],
        })
        stored = self.connections.get('answers')
        self.assertEqual(self.score(), baseline)
        self.assertEqual(self.connections.get('answers'), stored)


if __name__ == '__main__':
    unittest.main()
