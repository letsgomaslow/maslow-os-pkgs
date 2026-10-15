#!/usr/bin/env python3
"""No-network proof against an unpacked candidate, with RAM-only fake keys."""
import asyncio
import json
from pathlib import Path
import socket
import sys
import tempfile
import urllib.request
import urllib.error

package = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(package))
from maslow_free_ai.errors import FreeAIError
from maslow_free_ai.runtime import MODELS, RouterRuntime


class FakeKeys:
    def __init__(self):
        self.calls = 0
        self.fail = False

    async def get(self):
        self.calls += 1
        if self.fail:
            raise FreeAIError("KEYRING_LOCKED", "Synthetic locked key backend")
        return "a" * 64

    async def create(self, value):
        raise AssertionError("This proof must never create a credential")


async def main():
    evidence = {"syntheticKeysOnly": True, "outboundNetworkDisabled": True,
                "realKeyringVerified": False, "liveProviderVerified": False}
    with tempfile.TemporaryDirectory(prefix="maslow-packaged-proof-") as directory:
        keys = FakeKeys()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            runtime = RouterRuntime(Path(directory) / "state", package=package, keys=keys, port=port, grace=0.01)
            try:
                initial = runtime.status()
                assert initial["installed"] is True
                assert initial["ready"] is False
                assert initial["task_support"] is False  # no newly capable Voice in this container
                assert runtime.process is None and keys.calls == 0
                evidence["statusNoAutostart"] = True
                keys.fail = True
                try:
                    await runtime._start()
                    raise AssertionError("Locked key backend accepted")
                except FreeAIError as error:
                    assert error.code == "KEYRING_LOCKED"
                assert runtime.process is None
                evidence["keyFailureClosed"] = True
                keys.fail = False
                try:
                    await runtime._start()
                    raise AssertionError("Occupied port accepted")
                except FreeAIError as error:
                    assert error.code == "FREE_AI_PORT_OCCUPIED"
                assert runtime.process is None and listener.getsockname()[1] == port
                evidence["portCollisionPreservesListener"] = True
            finally:
                await runtime.close()
        # A real compiled child plus recorded synthetic configuration tests the
        # lifetime boundary. This override is not evidence of installed Voice.
        keys = FakeKeys()
        runtime = RouterRuntime(Path(directory) / "running", package=package, keys=keys, port=port, grace=0.01)
        runtime.task_supported = lambda: True
        try:
            route = await runtime._start("gsk_synthetic_packaged_00000000000000")
            process = runtime.process
            argv = Path(f"/proc/{process.pid}/cmdline").read_bytes()
            assert b"a" * 64 not in argv and route["token"].encode() not in argv
            assert b"gsk_synthetic" not in argv
            request = urllib.request.Request(route["endpoint"] + "/models", headers={"Authorization": "Bearer " + route["token"]})
            with urllib.request.urlopen(request, timeout=5) as response:
                models = json.load(response)["data"]
                assert len(models) == 2
            for endpoint, headers, body in (
                ("/models", {}, None),
                ("/models", {"Authorization": "Bearer " + route["token"], "Origin": "https://example.invalid"}, None),
                ("/chat/completions", {"Authorization": "Bearer " + route["token"], "Content-Type": "application/json"},
                 {"model": MODELS[0], "messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "https://example.invalid/image"}}]}]}),
            ):
                request = urllib.request.Request(route["endpoint"] + endpoint, headers=headers,
                    data=json.dumps(body).encode() if body else None)
                try:
                    urllib.request.urlopen(request, timeout=5)
                    raise AssertionError("Forbidden private-router request accepted")
                except urllib.error.HTTPError as error:
                    assert error.code in (400, 401, 403)
            assert b"gsk_synthetic" not in runtime.database.read_bytes()
            runtime.state.update(enabled=True, configured=True, free_plan="user-confirmed", verified_routes=list(MODELS))
            await runtime.acquire("synthetic-task")
            await runtime.release("synthetic-task")
            await asyncio.wait_for(asyncio.shield(runtime.idle_stop), 7)
            assert process.returncode is not None and runtime.process is None
            evidence.update(compiledRouterStarts=True, authenticatedLoopbackModels=True,
                            privateStdinBootstrap=True, ownedReleaseStopsRouter=True,
                            oldVoiceReadinessBlocked=True, authOriginMediaRejected=True)
        finally:
            await runtime.close()
    print(json.dumps(evidence, sort_keys=True))


asyncio.run(main())
