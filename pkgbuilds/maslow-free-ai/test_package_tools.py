import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("package_tools", Path(__file__).with_name("package-tools.py"))
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class PackageBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def production(self, dev=False):
        directory = self.root / "node_modules/better-sqlite3"
        directory.mkdir(parents=True)
        (directory / "package.json").write_text(json.dumps({"name": "better-sqlite3", "version": "12.10.0", "license": "MIT"}))
        (directory / "LICENSE").write_text("Synthetic notice")
        (self.root / "package-lock.json").write_text(json.dumps({"packages": {"node_modules/better-sqlite3": {"dev": dev}}}))
        self.lock = patch.object(tools, "LOCK", tools.digest(self.root / "package-lock.json"))
        self.lock.start()
        self.addCleanup(self.lock.stop)
        return directory

    def test_production_audit_requires_frozen_lock_and_rejects_development_deps(self):
        self.production()
        self.assertEqual("better-sqlite3", tools.installed_packages(self.root)[0]["name"])
        with patch.object(tools, "LOCK", "0" * 64), self.assertRaises(ValueError):
            tools.installed_packages(self.root)
        value = json.loads((self.root / "package-lock.json").read_text())
        value["packages"]["node_modules/better-sqlite3"]["dev"] = True
        (self.root / "package-lock.json").write_text(json.dumps(value))
        with patch.object(tools, "LOCK", tools.digest(self.root / "package-lock.json")), self.assertRaises(ValueError):
            tools.installed_packages(self.root)

    def test_production_links_must_remain_private_and_package_bins_are_absent(self):
        self.production()
        alias = self.root / "node_modules/escape"
        alias.symlink_to(self.root.parent)
        with self.assertRaises(ValueError):
            tools.installed_packages(self.root)
        alias.unlink()
        (self.root / "client").mkdir()
        alias.symlink_to(self.root / "client")
        with self.assertRaises(ValueError):
            tools.installed_packages(self.root)
        alias.unlink()
        (self.root / "node_modules/.bin").mkdir()
        with self.assertRaises(ValueError):
            tools.installed_packages(self.root)

    def test_workspace_nested_runtime_dependencies_are_audited(self):
        self.production()
        nested = self.root / "server/node_modules/ajv"
        nested.mkdir(parents=True)
        (nested / "package.json").write_text('{"name":"ajv","version":"8.20.0"}')
        lock = json.loads((self.root / "package-lock.json").read_text())
        lock["packages"]["server/node_modules/ajv"] = {"dev": False}
        (self.root / "package-lock.json").write_text(json.dumps(lock))
        with patch.object(tools, "LOCK", tools.digest(self.root / "package-lock.json")):
            records = tools.installed_packages(self.root)
            self.assertIn("server/node_modules/ajv", [item["path"] for item in records])
            lock["packages"]["server/node_modules/ajv"]["dev"] = True
            (self.root / "package-lock.json").write_text(json.dumps(lock))
            with patch.object(tools, "LOCK", tools.digest(self.root / "package-lock.json")), self.assertRaises(ValueError):
                tools.installed_packages(self.root)

    def test_attribution_preserves_actual_notices_and_records_gaps(self):
        directory = self.production()
        output = self.root / "notices"
        tools.notices(self.root, output)
        self.assertEqual("Synthetic notice", (output / "node_modules/better-sqlite3/LICENSE").read_text())
        self.assertEqual([], json.loads((output / "inventory.json").read_text())["missingNoticeFiles"])
        (directory / "LICENSE").unlink()
        tools.notices(self.root, output)
        self.assertEqual(["better-sqlite3"], json.loads((output / "inventory.json").read_text())["missingNoticeFiles"])

    def test_source_must_be_reviewed_and_match_exact_content(self):
        manifest = self.root / "manifest.json"
        for value in ({"schema": 1, "reviewed": False},
                      {"schema": 2, "reviewed": True},
                      {"schema": 1, "reviewed": True, "files": {"code": "old"}}):
            manifest.write_text(json.dumps(value))
            with patch.object(tools, "source_files", return_value={"code": "new"}), self.assertRaises(ValueError):
                tools.verify_source(self.root, manifest)
        manifest.write_text(json.dumps({"schema": 1, "reviewed": True, "files": {"code": "new"}}))
        with patch.object(tools, "source_files", return_value={"code": "new"}):
            tools.verify_source(self.root, manifest)

    def test_build_snapshot_preserves_verified_bytes_and_rejects_concurrent_change(self):
        source, output, manifest = self.root / "source", self.root / "snapshot", self.root / "manifest.json"
        source.mkdir()
        (source / "code").write_text("reviewed")
        files = {"code": tools.digest(source / "code")}
        manifest.write_text(json.dumps({"schema": 1, "reviewed": True, "files": files}))
        with patch.object(tools, "source_files", return_value=files):
            tools.snapshot_source(source, manifest, output)
        (source / "code").write_text("changed later")
        self.assertEqual("reviewed", (output / "code").read_text())
        with patch.object(tools, "source_files", return_value=files), self.assertRaises(ValueError):
            tools.snapshot_source(source, manifest, self.root / "changed-snapshot")

    def test_native_reuse_rejects_changed_dependency_bytes_modes_or_node(self):
        for workspace in ("freellmapi-" + tools.UPSTREAM, "production"):
            directory = self.root / workspace
            native = directory / "node_modules/better-sqlite3/build/Release/better_sqlite3.node"
            native.parent.mkdir(parents=True)
            native.write_bytes(b"synthetic native module")
            (directory / "package-lock.json").write_text("same frozen lock")
        node = self.root / ("node-v" + tools.NODE + "-linux-x64/bin/node")
        node.parent.mkdir(parents=True)
        node.write_bytes(b"synthetic Node")
        headers = self.root / ("node-v" + tools.NODE + "-linux-x64/include/node")
        headers.mkdir(parents=True)
        (headers / "node.h").write_text("synthetic headers")
        native = self.root / ("freellmapi-" + tools.UPSTREAM) / "node_modules/better-sqlite3/build/Release/better_sqlite3.node"
        manifest = self.root / "cache.json"
        lock = tools.digest(self.root / "production/package-lock.json")
        with patch.object(tools, "LOCK", lock):
            tools.write(manifest, tools.native_cache(self.root))
            tools.verify_native_cache(self.root, manifest)
            native.chmod(0o600)
            with self.assertRaises(ValueError):
                tools.verify_native_cache(self.root, manifest)
            native.chmod(0o644)
            native.write_bytes(b"changed addon")
            with self.assertRaises(ValueError):
                tools.verify_native_cache(self.root, manifest)
            native.write_bytes(b"synthetic native module")
            node.write_bytes(b"different Node")
            with self.assertRaises(ValueError):
                tools.verify_native_cache(self.root, manifest)

    def test_metadata_excludes_upstream_server_entry_and_claims_no_acceptance(self):
        manifest, audit, compiled, entry, output = [self.root / name for name in ("manifest", "audit", "compiled", "entry", "output")]
        manifest.write_text('{"reviewed":true}')
        audit.write_text('{}')
        entry.write_text('compiled synthetic module')
        for inputs in ({"server/dist/index.js": {}}, {"client/dist/main.js": {}}, {"server/dist/__tests__/test.js": {}}):
            compiled.write_text(json.dumps({"inputs": inputs}))
            with self.assertRaises(ValueError):
                tools.metadata(manifest, audit, compiled, entry, output)
        compiled.write_text(json.dumps({"inputs": {"server/dist/maslow-main.js": {}}}))
        tools.metadata(manifest, audit, compiled, entry, output)
        value = json.loads(output.read_text())
        self.assertFalse(value["taskSupportVerified"])
        self.assertFalse(value["liveProviderVerified"])
        self.assertEqual(tools.digest(entry), value["entrySha256"])

    def test_production_lock_rejects_orphan_workspaces_and_unapproved_versions(self):
        original, production, output = [self.root / name for name in ("original.json", "production.json", "review.json")]
        records = {"node_modules/" + name: {"version": version} for name, version in tools.FIXES.items()}
        original.write_text(json.dumps({"packages": records}))
        production.write_text(json.dumps({"packages": {**records, "client": {"name": "unused"}}}))
        with patch.object(tools, "LOCK", tools.digest(original)), patch.object(tools, "PRODUCTION_LOCK", tools.digest(production)), self.assertRaises(ValueError):
            tools.review_production_lock(original, production, output)
        extra = {**records, "node_modules/unreviewed": {"version": "9.9.9"}}
        production.write_text(json.dumps({"packages": extra}))
        with patch.object(tools, "LOCK", tools.digest(original)), patch.object(tools, "PRODUCTION_LOCK", tools.digest(production)), self.assertRaises(ValueError):
            tools.review_production_lock(original, production, output)


if __name__ == "__main__":
    unittest.main()
