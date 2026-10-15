import importlib.util
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("source_tools", Path(__file__).with_name("source-tools.py"))
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class SourceIntegrityTests(unittest.TestCase):
    def test_cache_aliases_are_rejected_before_filtering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = root / "voice/maslow_voice"
            code.mkdir(parents=True)
            for name in ("__pycache__", "injected.pyc"):
                link = code / name
                link.symlink_to(root)
                with self.assertRaisesRegex(ValueError, "Aliased Voice source"):
                    tools.source_files(root)
                link.unlink()
            (code / "injected.pyc").write_bytes(b"unreviewed bytecode")
            with self.assertRaisesRegex(ValueError, "Unreviewed sourceless bytecode"):
                tools.source_files(root)

    def test_fresh_cache_prefix_executes_source_instead_of_tampered_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = root / "cache_probe.py"
            code.write_text("answer = 99\n")
            timestamp = code.stat().st_mtime_ns
            py_compile.compile(str(code), doraise=True,
                               invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
            code.write_text("answer = 42\n")
            os.utime(code, ns=(timestamp, timestamp))
            command = [sys.executable, "-c", "import cache_probe; print(cache_probe.answer)"]
            env = {**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"}
            env.pop("PYTHONPYCACHEPREFIX", None)
            self.assertEqual("99", subprocess.check_output(command, env=env, cwd=root, text=True).strip())
            with tempfile.TemporaryDirectory(dir=root, prefix="fresh-cache-") as prefix:
                env["PYTHONPYCACHEPREFIX"] = prefix
                self.assertEqual("42", subprocess.check_output(command, env=env, cwd=root, text=True).strip())

    def test_isolated_check_does_not_execute_source_startup_hook(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'startup-marker'
            (root / 'sitecustomize.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').touch()\n')
            (root / 'checked.py').write_text('answer=42\n')
            env = {**os.environ,'PYTHONPATH':str(root)}
            with tempfile.TemporaryDirectory(prefix='cache-') as cache:
                result = subprocess.check_output([sys.executable,'-I','-B','-X','pycache_prefix='+cache,
                    '-c','import sys; sys.path.insert(0,sys.argv[1]); import checked; print(checked.answer)',str(root)],
                    env=env,cwd=root,text=True)
            self.assertEqual(result.strip(),'42')
            self.assertFalse(marker.exists())

    def test_import_cache_does_not_invalidate_source_but_new_code_does(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("voice/maslow_voice", "voice/hermes_plugin", "voice/assistant_plugin",
                         "voice/assets", "voice/ui", "voice/tests", "free_ai/maslow_free_ai"):
                (root / name).mkdir(parents=True)
            for name in ("LICENSE", "voice/assistant_worker.py", "voice/requirements.lock",
                         "voice/bin/omarchy-voice-control", "bin/omarchy-launch-voice",
                         "voice/systemd/maslow-voice.service", "test/shell.d/base-test.sh",
                         "test/shell.d/voice-test.sh"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic input")
            code = root / "voice/maslow_voice/cache_probe.py"
            code.write_text("answer = 42\n")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema": 1, "reviewed": True,
                                            "files": tools.source_files(root)}))
            tools.verify(root, manifest)
            for name in ('voice/sitecustomize.py','free_ai/sitecustomize.py'):
                injected = root / name
                injected.write_text('unreviewed=True\n')
                with self.assertRaises(ValueError):
                    tools.verify(root,manifest)
                injected.unlink()
            pipe = root / 'voice/maslow_voice/unreviewed.pipe'
            os.mkfifo(pipe)
            with self.assertRaisesRegex(ValueError,'Nonregular Voice source'):
                tools.verify(root,manifest)
            pipe.unlink()
            cache = root / 'voice/ui/__pycache__'
            cache.mkdir()
            with self.assertRaisesRegex(ValueError,'Unexpected cache source'):
                tools.verify(root,manifest)
            cache.rmdir()
            cache = root / 'voice/tests/__pycache__'
            cache.mkdir()
            for name in ('__init__.py','test_injected.py','unreviewed-tool'):
                injected = cache / name
                injected.write_text('unreviewed=True\n')
                with self.assertRaisesRegex(ValueError,'Executable or data source in cache'):
                    tools.verify(root,manifest)
                injected.unlink()
            cache.rmdir()
            imported = importlib.util.spec_from_file_location("cache_probe", code)
            module = importlib.util.module_from_spec(imported)
            imported.loader.exec_module(module)
            self.assertEqual(42, module.answer)
            self.assertTrue(list(code.parent.rglob("*.pyc")))
            tools.verify(root, manifest)
            (root / "free_ai/maslow_free_ai/new_backend.py").write_text("changed = True\n")
            with self.assertRaises(ValueError):
                tools.verify(root, manifest)

    def test_unreviewed_or_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            with patch.object(tools, "source_files", return_value={"voice/code.py": "new"}):
                for value in ({"schema": 1, "reviewed": False},
                              {"schema": 2, "reviewed": True},
                              {"schema": 1, "reviewed": True, "files": {"voice/code.py": "old"}}):
                    manifest.write_text(json.dumps(value))
                    with self.assertRaises(ValueError):
                        tools.verify(root, manifest)
                manifest.write_text(json.dumps({"schema": 1, "reviewed": True,
                                                "files": {"voice/code.py": "new"}}))
                tools.verify(root, manifest)

    def test_missing_or_aliased_source_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                tools.source_files(root)
            (root / "voice").mkdir()
            (root / "elsewhere").mkdir()
            (root / "voice/maslow_voice").symlink_to(root / "elsewhere")
            with self.assertRaises(ValueError):
                tools.source_files(root)


if __name__ == "__main__":
    unittest.main()
