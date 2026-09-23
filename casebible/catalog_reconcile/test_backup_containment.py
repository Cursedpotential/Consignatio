"""Byline: Codex | 2026-09-20. Retention checks must not discard unique records."""
import collections
import unittest
from defusedxml import ElementTree
from compare_backup_iterations import canonical, fingerprint, compare

class ContainmentTests(unittest.TestCase):
    def assessment(self, name):
        return {'name':name,'sha256':name,'parse_error':None,'declared_count_matches':True,'metadata_stable':True}
    def test_complete_multiset_subset(self):
        r=compare(self.assessment('old'),self.assessment('new'),collections.Counter(a=2),collections.Counter(a=2,b=1))
        self.assertEqual(r['status'],'skip_additional_binary_copy_proven_record_subset')
    def test_duplicate_multiplicity_is_preserved(self):
        r=compare(self.assessment('old'),self.assessment('new'),collections.Counter(a=2),collections.Counter(a=1))
        self.assertEqual(r['missing_record_instances'],1)
        self.assertEqual(r['status'],'retain_separately_unproven_subset')
    def test_incomplete_backup_cannot_be_superseded(self):
        old=self.assessment('old');old['parse_error']={'position':[1,1]}
        r=compare(old,self.assessment('new'),collections.Counter(a=1),collections.Counter(a=1))
        self.assertEqual(r['status'],'retain_separately_unproven_subset')
    def test_metadata_difference_changes_identity(self):
        a=ElementTree.fromstring('<sms date="1" body="same" read="0"/>')
        b=ElementTree.fromstring('<sms date="1" body="same" read="1"/>')
        self.assertNotEqual(fingerprint(canonical(a)),fingerprint(canonical(b)))
    def test_nested_payload_difference_changes_identity(self):
        a=ElementTree.fromstring('<mms><parts><part data="YQ=="/></parts></mms>')
        b=ElementTree.fromstring('<mms><parts><part data="Yg=="/></parts></mms>')
        self.assertNotEqual(fingerprint(canonical(a)),fingerprint(canonical(b)))
    def test_backup_source_change_blocks_supersession(self):
        old=self.assessment('old');old['metadata_stable']=False
        r=compare(old,self.assessment('new'),collections.Counter(a=1),collections.Counter(a=2))
        self.assertEqual(r['status'],'retain_separately_unproven_subset')

if __name__=='__main__':unittest.main()
