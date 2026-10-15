#!/usr/bin/env python3
"""Recipe-local integrity, production closure and attribution checks."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

UPSTREAM = "65ec96df6450224a95a0eabfff8b41b394b2396f"
LOCK = "3e6265bd3a3346ca362fd54405e5ed404df72e6a0002cd07d2390dce54463038"
PRODUCTION_LOCK = "843dcda1e14f77c8fea99598d1f16b4846b9a3c0d95bdaccc9539f8f3c63946e"
NODE = "22.23.3"
FIXES = {"fast-uri": "3.1.8", "proxy-addr": "2.0.8", "qs": "6.16.0", "multer": "2.4.0"}
SAFETY_TRANSITIVES = {"side-channel": "1.1.1"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def source_files(root):
    files = [root / "LICENSE"]
    files += list((root / "free_ai/maslow_free_ai").glob("*.py"))
    files += [root / "free_ai/bin/omarchy-free-ai", root / "free_ai/router/upstream.patch"]
    files += list((root / "free_ai/router/src").rglob("*.ts"))
    files += [root / "free_ai/tests/router-boundary.test.ts", root / "free_ai/tests/router-bootstrap.test.mjs"]
    if not (root / "free_ai/maslow_free_ai/control.py").is_file() or len(files) < 12:
        raise ValueError("Complete reviewed runtime adapter source is required")
    for path in files:
        if not path.is_file() or path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError("Source must contain regular unaliased files")
    return {str(path.relative_to(root)): digest(path) for path in sorted(files)}


def verify_source(root, manifest):
    value = json.loads(manifest.read_text())
    if value.get("schema") != 1 or value.get("reviewed") is not True:
        raise ValueError("Source manifest is pending coordinator review; do not build")
    if source_files(root) != value.get("files"):
        raise ValueError("Runtime adapter differs from exact reviewed source manifest")


def snapshot_source(root, manifest, output):
    verify_source(root, manifest)
    value = json.loads(manifest.read_text())
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for relative, expected in value["files"].items():
        # Rehash the bytes copied, rather than returning to a live worktree
        # during check/package after prepare's initial verification.
        data = (root / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Runtime source changed while taking the build snapshot")
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    verify_source(output, manifest)


def native_cache(root):
    files = {}
    for workspace in ("freellmapi-" + UPSTREAM,):
        directory = root / workspace
        if digest(directory / "package-lock.json") != LOCK:
            raise ValueError("Cannot reuse dependencies with a different lock")
        native = directory / "node_modules/better-sqlite3/build/Release/better_sqlite3.node"
        if not native.is_file():
            raise ValueError("Rebuilt source-workspace SQLite is required")
        for modules in module_roots(directory):
            for path in sorted(modules.rglob("*")):
                relative = str(path.relative_to(root))
                if path.is_symlink():
                    files[relative] = {"link": str(path.readlink())}
                elif path.is_file():
                    files[relative] = {"sha256": digest(path), "mode": path.stat().st_mode & 0o777}
    headers = root / ("node-v" + NODE + "-linux-x64/include/node")
    if not (headers / "node.h").is_file():
        raise ValueError("Exact private Node build headers are required")
    for path in sorted(headers.rglob("*")):
        if path.is_file():
            files[str(path.relative_to(root))] = {"sha256": digest(path), "mode": path.stat().st_mode & 0o777}
    return {"schema": 1, "lockSha256": LOCK, "nodeVersion": NODE, "nodeModuleAbi": "127",
            "nodeBinarySha256": digest(root / ("node-v" + NODE + "-linux-x64/bin/node")), "files": files}


def verify_native_cache(root, manifest):
    if native_cache(root) != json.loads(manifest.read_text()):
        raise ValueError("Dependency or native cache differs from the preserved exact build")


def module_roots(root):
    return [path for path in (root / "node_modules", root / "server/node_modules", root / "shared/node_modules") if path.is_dir()]


def installed_packages(root):
    roots = module_roots(root)
    lock = json.loads((root / "package-lock.json").read_text())
    if digest(root / "package-lock.json") not in (LOCK, PRODUCTION_LOCK):
        raise ValueError("Production dependency lock changed")
    result = []
    for path in sorted(path for modules in roots for path in modules.rglob("package.json")):
        # A dependency's fixture manifests are not installed dependency packages.
        directory = path.parent
        relative = str(directory.relative_to(root))
        if relative not in lock["packages"]:
            parts = directory.relative_to(root).parts
            tail = parts[max(index for index, part in enumerate(parts) if part == "node_modules") + 1:]
            if len(tail) == 1 or len(tail) == 2 and tail[0].startswith("@"):
                raise ValueError("Unrecorded installed package reached production closure: " + relative)
            continue
        record = lock["packages"][relative]
        if record.get("dev") is True:
            raise ValueError("Development dependency reached production closure: " + relative)
        package = json.loads(path.read_text())
        if package.get("name") in ("electron", "npm", "typescript", "vitest", "tsx", "esbuild", "concurrently", "jsdom"):
            raise ValueError("Development or unrelated workspace tooling reached package")
        result.append({"path": relative, "name": package.get("name", relative),
                       "version": package.get("version"), "license": package.get("license"),
                       "integrity": record.get("integrity"), "resolved": record.get("resolved")})
    for path in (path for modules in roots for path in modules.rglob("*")):
        if path.is_symlink():
            target = path.resolve(strict=True)
            if not target.is_relative_to(root.resolve()):
                raise ValueError("Production dependency link escapes private router")
            if not any(target.is_relative_to(modules.resolve()) for modules in roots) and target not in (root / "server", root / "shared"):
                raise ValueError("Unrelated workspace link reached production closure")
        if path.name == ".bin":
            raise ValueError("Package bin launchers reached runtime closure")
    if not any(item["name"] == "better-sqlite3" for item in result):
        raise ValueError("Required SQLite production dependency is missing")
    return result


def audit_production(root, output):
    packages = installed_packages(root)
    write(output, {"schema": 1, "nodeVersion": NODE, "lockSha256": digest(root / "package-lock.json"),
                   "sourceLockSha256": LOCK,
                   "packages": packages, "packageCount": len(packages),
                   "workspacePackages": ["@freellmapi/server"],
                   "totalPackageCount": len(packages) + 1})


def review_production_lock(original, production, output):
    if digest(original) != LOCK or digest(production) != PRODUCTION_LOCK:
        raise ValueError("Source or production lock differs from pinned bytes")
    old = json.loads(original.read_text())["packages"]
    new = json.loads(production.read_text())["packages"]
    if any("node_modules/" not in key and key not in ("", "server") for key in new):
        raise ValueError("Unrelated workspace metadata reached production lock")
    old_pairs = {(record.get("name") or key.split("node_modules/")[-1], record.get("version"))
                 for key, record in old.items() if "node_modules/" in key and not record.get("link")}
    added, retained = [], []
    for key, record in new.items():
        if "node_modules/" not in key or record.get("link"):
            continue
        name = record.get("name") or key.split("node_modules/")[-1]
        version = record.get("version")
        if name in FIXES and version != FIXES[name]:
            raise ValueError("Vulnerable version remains in production lock: " + name)
        if (name, version) not in old_pairs and FIXES.get(name) != version and SAFETY_TRANSITIVES.get(name) != version:
            raise ValueError("Unreviewed dependency version change: " + name)
        if (name, version) in old_pairs and not any(
            (entry.get("name") or path.split("node_modules/")[-1], entry.get("version")) == (name, version)
            and entry.get("resolved") == record.get("resolved") and entry.get("integrity") == record.get("integrity")
            for path, entry in old.items() if "node_modules/" in path):
            raise ValueError("Retained dependency artifact changed: " + name)
        (added if (name, version) not in old_pairs else retained).append({"name": name, "version": version, "path": key})
    for name, version in FIXES.items():
        if not any(key.endswith("/" + name) and record.get("version") == version for key, record in new.items()):
            raise ValueError("Required safety pin missing: " + name)
    forbidden = ("sharp", "compression", "undici", "socks-proxy-agent", "ip-address")
    if any(key.endswith("/" + name) for key in new for name in forbidden):
        raise ValueError("Unused dependency root retained")
    write(output, {"schema": 1, "sourceLockSha256": LOCK, "productionLockSha256": PRODUCTION_LOCK,
                   "approvedSafetyPins": FIXES, "newVersionPairs": added, "retainedVersionPairs": retained,
                   "requiredSafetyTransitives": SAFETY_TRANSITIVES,
                   "removedUnusedRoots": list(forbidden), "originalSourceLockUnchanged": True})


def notices(root, output):
    records = installed_packages(root)
    missing = []
    for record in records:
        directory = root / record["path"]
        selected = []
        # Some platform libraries put their constituent notices below lib/.
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.is_symlink() or "node_modules" in path.relative_to(directory).parts:
                continue
            name = path.name.upper()
            if name.startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE", "COPYRIGHT")):
                relative = path.relative_to(directory)
                target = output / record["path"] / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                selected.append(str(relative))
        if not selected:
            missing.append(record["name"])
            # Preserve the actual pinned libvips constituent licensing table,
            # while retaining the full-notice gap for separate release review.
            readme = directory / "README.md"
            if record["name"].startswith("@img/sharp-libvips-") and readme.is_file() and "## Licensing" in readme.read_text():
                target = output / record["path"] / "README.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(readme, target)
                selected.append("README.md")
                record["licenseSummaryOnly"] = True
        record["noticeFiles"] = selected
    write(output / "inventory.json", {"schema": 1, "packages": records,
                                      "missingNoticeFiles": missing,
                                      "review": "Dependency notices require release review; metadata alone is not legal acceptance."})


def metadata(manifest, audit, compiled, entry, output):
    source = json.loads(manifest.read_text())
    dependencies = json.loads(audit.read_text())
    inputs = json.loads(compiled.read_text())["inputs"]
    if any(not name.startswith("server/dist/") or "/__tests__/" in name or name.endswith("/index.js") and name == "server/dist/index.js" for name in inputs):
        raise ValueError("Unexpected compiled entry input")
    write(output, {"schema": 1, "experimental": True, "upstreamCommit": UPSTREAM,
                   "upstreamArchiveSha256": "b64d80d409c6ae6f696f356a4c2f19fd75a44e30268e3566ade6088229f52e9e",
                   "lockSha256": LOCK, "nodeVersion": NODE,
                   "productionLockSha256": PRODUCTION_LOCK, "approvedSafetyPins": FIXES,
                   "requiredSafetyTransitives": SAFETY_TRANSITIVES,
                   "omittedOptionalMediaImport": "sharp",
                   "nodeModuleAbi": "127", "sourceManifestSha256": digest(manifest),
                   "minimumNativeRuntime": {"glibc": "2.44", "GLIBCXX": "3.4.30"},
                   "nodeArchiveSha256": "df450af89261115ef9f9e3830c3eeb2cc9213b63c720b1af623cb5dcbe2e02de",
                   "source": source, "productionDependencies": dependencies,
                   "compiledInputs": inputs, "entrySha256": digest(entry),
                   "requiredVoiceCapabilities": ["task_submit", "typed-tasks-independent-of-audio", "execution_connection:free-cloud"],
                   "taskSupportVerified": False, "liveProviderVerified": False,
                   "deliveryVerified": False})


if __name__ == "__main__":
    action, *args = sys.argv[1:]
    try:
        if action == "freeze-source":
            root, output = map(Path, args)
            write(output, {"schema": 1, "reviewed": False, "files": source_files(root)})
        elif action == "verify-source":
            verify_source(*map(Path, args))
        elif action == "snapshot-source":
            snapshot_source(*map(Path, args))
        elif action == "freeze-native-cache":
            root, output = map(Path, args)
            write(output, native_cache(root))
        elif action == "verify-native-cache":
            verify_native_cache(*map(Path, args))
        elif action == "audit-production":
            audit_production(*map(Path, args))
        elif action == "review-production-lock":
            review_production_lock(*map(Path, args))
        elif action == "notices":
            notices(*map(Path, args))
        elif action == "metadata":
            metadata(*map(Path, args))
        else:
            raise ValueError("Unknown recipe operation")
    except (OSError, ValueError, KeyError) as error:
        sys.exit("Package verification failed: " + str(error))
