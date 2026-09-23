"""Byline: Codex | 2026-09-20. Historical recovery identity guards."""
import unittest
from recover_historical import safe_name,verify_headers


class RecoveryTests(unittest.TestCase):
    def test_version_mismatch_rejected(self):
        with self.assertRaises(ValueError):verify_headers({'X-Bz-File-Id':'wrong','Content-Length':'3','X-Bz-Content-Sha1':'a'*40},{'selected_version':{'file_id':'right'},'size':3,'sha1':'a'*40})
    def test_size_mismatch_rejected(self):
        with self.assertRaises(ValueError):verify_headers({'X-Bz-File-Id':'right','Content-Length':'4','X-Bz-Content-Sha1':'a'*40},{'selected_version':{'file_id':'right'},'size':3,'sha1':'a'*40})
    def test_hash_mismatch_rejected(self):
        with self.assertRaises(ValueError):verify_headers({'X-Bz-File-Id':'right','Content-Length':'3','X-Bz-Content-Sha1':'b'*40},{'selected_version':{'file_id':'right'},'size':3,'sha1':'a'*40})
    def test_safe_leaf(self):
        for key in ('folder/../../CON','folder/a:b?.txt','folder/..','folder/NUL.txt'):
            leaf=safe_name(key)
            self.assertNotIn('/',leaf);self.assertNotIn('\\',leaf);self.assertNotIn(':',leaf);self.assertNotIn(leaf,('CON','NUL.txt','..'))


if __name__=='__main__':unittest.main()
