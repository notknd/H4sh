import tempfile
import unittest
from pathlib import Path

from h4sh.core.reporter import export
from h4sh.core.privacy import mask_phone
from h4sh.core.store import EvidenceStore
from h4sh.core.validation import target_host, web_url


class CoreTests(unittest.TestCase):
    def test_target_validation_rejects_shell_syntax(self):
        self.assertEqual(target_host("Example.ORG."), "example.org")
        with self.assertRaises(ValueError):
            target_host("example.org; id")
        with self.assertRaises(ValueError):
            target_host("https://example.org")

    def test_web_url_requires_http_scheme(self):
        self.assertEqual(web_url("https://example.org/test"), "https://example.org/test")
        with self.assertRaises(ValueError):
            web_url("file:///etc/passwd")

    def test_store_and_report_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = EvidenceStore(root / "logs")
            store.add("test", "example.org", {"ok": True})
            files = export(store.session(), root / "reports")
            self.assertEqual(len(files), 3)
            self.assertTrue(all(path.exists() for path in files))

    def test_cases_are_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            store = EvidenceStore(Path(folder) / "logs")
            store.add("one", "a", {}, "Caso A")
            store.add("two", "b", {}, "Caso B")
            self.assertEqual([item["module"] for item in store.session("Caso A")], ["one"])
            self.assertIn("Caso A", store.cases())

    def test_phone_masking(self):
        self.assertEqual(mask_phone("+55 11 99999-1234"), "••••••1234")


if __name__ == "__main__":
    unittest.main()
