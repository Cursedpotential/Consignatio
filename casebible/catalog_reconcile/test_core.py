"""Byline: Codex | 2026-09-20. Reconciliation safety invariants."""
import unittest
from core import VersionIndex,digest,occurrence,source_sha1,stable_id
from io_utils import B2


def obj(identity,key,sha,size,visible=True,action="upload"):
    return dict(file_id=identity,key=key,sha1=sha,size=size,visible=visible,action=action)


class ReconciliationTests(unittest.TestCase):
    def test_old_version_not_lost_when_path_replaced(self):
        index=VersionIndex([obj("old","p","a"*40,248,False),obj("new","p","b"*40,8892)])
        self.assertEqual(index.resolve("p","a"*40,248),("historical_exact","b2_sha1_size",["old"]))

    def test_wrong_size_is_not_identity(self):
        index=VersionIndex([obj("new","p","a"*40,249)])
        self.assertEqual(index.resolve("p","a"*40,248)[0],"identity_conflict")

    def test_same_size_and_name_is_not_identity(self):
        index=VersionIndex([obj("new","p",None,248)])
        self.assertEqual(index.resolve("p",None,248)[0],"path_only_unverified")

    def test_retains_all_occurrences_and_alternatives(self):
        index=VersionIndex([obj("one","p","a"*40,5),obj("two","q","a"*40,5)])
        self.assertEqual(set(index.resolve("p","a"*40,5)[2]),{"one","two"})
        self.assertNotEqual(stable_id("drive","A"),stable_id("drive","B"))

    def test_hide_marker_is_not_a_content_match(self):
        index=VersionIndex([obj("hide","p","a"*40,5,False,"hide")])
        self.assertEqual(index.resolve("p","a"*40,5)[0],"unresolved_identity")

    def test_algorithms_not_interchangeable(self):
        self.assertIsNone(digest("a"*32,40));self.assertIsNone(digest("none",40))
        self.assertEqual(source_sha1({"contentSha1":"none","fileInfo":{"large_file_sha1":"B"*40}}),"b"*40)

    def test_native_export_conflict_not_missing_content_assertion(self):
        raw=dict(source="gdrive/salem85",scope="",path="doc",source_id="id",metadata={"native":True},disposition="exported",size=-1)
        linked=occurrence(raw,VersionIndex([]))
        self.assertIn("native_export_linkage_conflict",linked["quality_flags"])
        self.assertEqual(linked["retirement_status"],"not_cleared")
        self.assertEqual(linked["bas_status"],"not_assessed")

    def test_b2_mutations_and_content_downloads_rejected(self):
        instance=object.__new__(B2)
        for method in ("b2_delete_file_version","b2_copy_file","b2_download_file_by_id","b2_update_bucket"):
            with self.assertRaises(ValueError):instance.call(method,{})

    def test_duplicate_version_id_rejected(self):
        row=obj('same','p','a'*40,5)
        with self.assertRaises(ValueError):VersionIndex([row,row])

    def test_missing_size_cannot_match_hash(self):
        index=VersionIndex([obj('v','p','a'*40,5)])
        self.assertEqual(index.resolve('p','a'*40,None)[0],'identity_conflict')


if __name__=="__main__":unittest.main()
