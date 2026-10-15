# Accepted Hub 2 packaging baseline

The accepted Lenovo local preview is Hub **2.0.3-1**, Voice **0.1.5-44**, Free AI **0.1.0-3**. Future packaging iterations preserve this combination and the Hub2 native experience. Hub/runtime source product branches are `main`; this repository's product branch is **`maslow`**, with `master` reserved for upstream.

## Scope and provenance

This scoped integration copies only the Git-tracked `pkgbuilds/maslow-hub`, `pkgbuilds/maslow-voice` and `pkgbuilds/maslow-free-ai` inputs from reviewed recipe revision `6a681df2e8b4df0f62c26bcb3022602281a6db29`, then takes the backend3 `PKGBUILD`, `README.md` and `source-integrity.json` from `18d0e104465e3d78bd00c932625d058ca4fa9c9a`. Recipe/tool/data bytes and modes remain exact; Voice and backend README status amendments are intentional prose-only exceptions. The broader feature branch's unfinished Connect recipes/history are excluded. Keeping a recipe in a feature branch is not approval to publish it.

| Component | Reviewed source | Source archive SHA-256 |
| --- | --- | --- |
| Voice44 | runtime `a8afb84f21dfd03a15730f7c4c08b1e2ac4551da` | `79d53d783d6a56c1583f5f4626c887a51ed70c242ddcd8c6a85bf23d8a45387e` |
| Backend3 | runtime `a41012c6b207ac912eb034b813834485efe094f9` | `4dd74a9f5cfaf4a8ded2057e59c973d4da511feb81ac558799170f6bbaef5bf4` |
| Hub2.0.3 | Hub `93458a5d7ad9c7a34a7c2ecca298b9611ced4a39` plus reviewed local QA export | supplied explicitly through `MASLOW_HUB_SRC`; version derives from `release/version.json` |

Backend3 changes the reviewed recovery verifier's IV width only; Node/router/dependencies/schema/ownership remain unchanged. Voice44 adds passive Hub adapter/control support while retaining Voice UI/audio, SDK locks and dependencies. Preserve those source manifests and archive pins; later docs/merge commits are not replacement build inputs.

The installed Hub archive SHA-256 is `ac9f734f6305e03c91d8d89a03ac410894d733afcd53fdc625270e09efa00ab7` (335,123,494 bytes;62 mapped files/90 members). Its supervised local export differs from product source only in two reviewed V1 QA literals; product V1/V2 acceptance gates stay closed. Optional signed bundles remain inert Hub-owned data until a separately checked owning action. No private keys or credentials are recipe inputs.

## Verification and limits

Existing exact-input build/audit evidence is retained, rather than rebuilding unchanged packages for documentation/source integration. Hub754 Python tests and UI contracts pass. The owning recovery prerequisite was settled; installed native Hub203 and normal canonical203→202 rollback/203 reapply passed. Both roundtrip checkpoints preserve8 tasks,494 events and five preference files exactly; Updates reopened on the same shell process and ended Up to date/idle/transactionnull. The runtime `docs/maslow-development.md` and October13–15 handoff own detailed evidence and limits. Source merge is not a rebuilt ISO, published channel, live provider/audio acceptance or wider Free AI completion.

Before changing these inputs: compare exact recipe file bytes/modes, run `git diff --check`, `bash -n` on the three recipes, `./test/maslow-packaging`, both recipe Python suites, and both source validators against the retained reviewed inputs. New package behavior/dependencies/ownership requires relevant new builds and overlap/native acceptance; do not weaken validators. Hub owns its canonical identity/six journeys and privileged delivery/recovery orchestration; runtime supplies backend snapshot/restore and Voice lifecycle support, and Voice owns conversation/tasks/audio. Connect stays separate/gated; Craft remains paused.
