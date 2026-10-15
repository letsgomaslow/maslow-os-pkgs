"""Verify the exact reviewed Voice production and owning-check inputs."""
import hashlib
import json
from pathlib import Path
import stat
import sys


def source_files(root):
    files = []
    for name in ("voice", "free_ai"):
        directory = root / name
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("Missing unaliased Voice source directory: " + name)
        for path in directory.rglob("*"):
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError("Aliased Voice source: " + str(path))
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError("Nonregular Voice source: " + str(path))
            # Imports may populate caches between check and package. The recipe
            # strips them from shipped files; they are not reviewed source.
            if "__pycache__" in path.relative_to(root).parts:
                relative = path.relative_to(root).parts
                if relative[:2] not in {('voice','maslow_voice'),('voice','hermes_plugin'),
                        ('voice','assistant_plugin'),('voice','tests'),('voice','dev'),
                        ('free_ai','maslow_free_ai'),('free_ai','tests')}:
                    raise ValueError("Unexpected cache source: " + str(path))
                if stat.S_ISREG(mode) and path.suffix not in ('.pyc','.pyo'):
                    raise ValueError("Executable or data source in cache: " + str(path))
                continue
            if path.suffix in (".pyc", ".pyo"):
                raise ValueError("Unreviewed sourceless bytecode: " + str(path))
            if path.is_file():
                files.append(path)
    files += [root / name for name in (
        "LICENSE", "voice/assistant_worker.py", "voice/requirements.lock",
        "voice/bin/omarchy-voice-control", "bin/omarchy-launch-voice",
        "voice/systemd/maslow-voice.service", "test/shell.d/base-test.sh",
        "test/shell.d/voice-test.sh")]
    result = {}
    for path in sorted(files):
        if not path.is_file() or path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("Missing regular unaliased Voice source: " + str(path))
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify(root, manifest):
    value = json.loads(manifest.read_text())
    if value.get("schema") != 1 or value.get("reviewed") is not True:
        raise ValueError("Voice source is not reviewed")
    if source_files(root) != value.get("files"):
        raise ValueError("Voice source differs from the exact reviewed manifest")


if __name__ == "__main__":
    try:
        verify(Path(sys.argv[1]), Path(sys.argv[2]))
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
