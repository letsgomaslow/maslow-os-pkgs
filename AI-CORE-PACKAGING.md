# AI core packaging

This is local-source candidate work, not a signed or published Maslow package channel. Package tests, package execution, and full installed-image acceptance are separate gates.

## Ownership

`openai-codex-bin` owns `/usr/bin/codex`; `claude-code` owns `/usr/bin/claude` and its vendor binary under `/opt/claude-code`. Arch supplies the Bitwarden desktop package. The Bitwarden CLI is not a prerequisite for onboarding and is not added.

`hermes-agent` uses the upstream source-checkout layout under `/opt/hermes-agent/app`, with a private relocatable Python interpreter under `/opt/hermes-agent/python` and `/usr/bin/hermes` as its launcher. It does not replace Arch Python, write a user's home during installation, install a gateway service, or configure provider accounts. Runtime wrapper migration belongs to the runtime repository and must preserve unowned files.

## Hermes inputs

- Official Hermes tag `v2026.8.31`, commit `6e8f8418e6378eb2617e4de074e13dedd091b8af`, metadata version `0.21.0`; MIT license.
- Official Astral python-build-standalone `3.13.15+20260901` Linux x86_64 GNU install-only archive; the archive and Python license are retained in the package layout. The PKGBUILD pins the published asset SHA-256.
- The source archive includes `uv.lock`. Export only the core closure, without extras or development groups, and require hashes for its installation. Disable project override discovery during that installation so the lock's exact versions, rather than range overrides, are authoritative.
- The source `package-lock.json` drives `npm ci` for only the terminal/shared workspaces. Build the self-contained TUI using the upstream script; do not ship node_modules or Electron. Node remains a declared runtime dependency.

Upstream explicitly rejects generic wheels because they omit runtime assets. Do not bypass that guard with `HERMES_NIX_BUILD`. The source-layout package retains bundled skills, locales, plugin manifests, optional-integration definitions, and terminal assets. These definitions do not install optional services or Python extras. The web dashboard is not part of this CLI package.

The previous `v2026.8.18` source (metadata `0.20.4`) built its terminal frontend but failed the native interactive-query capability check. It must not be substituted simply because its basic version command works.

## Acceptance

Run `bash test/ai-core-packaging`, `bash test/maslow-packaging`, and `makepkg` for every changed recipe. All source checksums must pass. Then run the ISO repository's package-file overlap checker on the actual artifacts, install with pacman, and check `/usr/bin` ownership and executable behavior with networking disabled and a fresh home.

Before claiming AI-ready installation, complete the runtime installed-image acceptance test on the fresh ISO. An emulated container's successful build does not override a failing executable or a failed package hook. Provider authentication and an actual AI workload remain user-led checks; do not infer them from installation or version output.

## Distribution notices

Codex `0.152.0-2` delivers the official release's SHA-256-pinned `LICENSE` and `NOTICE` under `/usr/share/licenses/openai-codex-bin`. This notice-only revision leaves both vendor executables unchanged. The internal 2026-09-04 test ISO used `0.152.0-1`; this follow-up is not included in that frozen image.

An installed-artifact inventory found license or notice files in 62 of 63 Hermes Python distribution metadata directories (including the standalone runtime's pip). The remaining `firecrawl-anydoc 0.2.4` wheel declares MIT in metadata but contains no license file in its recorded distribution files. The package retains Hermes and Python licenses plus dependency-provided files, including Requests' NOTICE, Cryptography's Apache/BSD texts, and tqdm's `LICENCE` (MPL-2.0 and MIT). Retention is evidence, not a completed compliance audit.

The bundled terminal JavaScript retains dependency license comments, but some comments reference a separate upstream LICENSE that is not shipped with the self-contained bundle. Before public distribution, inventory the exact bundled JavaScript dependencies and standalone Python native libraries, supply missing required notices, and determine any applicable source-delivery obligations. Do not infer that the top-level MIT/PSF identifiers cover every bundled component. This does not authorize publishing the current internal image or altering upstream account terms.
