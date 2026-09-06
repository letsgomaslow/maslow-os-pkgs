# Maslow OS Packages

This repository contains the recipes used to build software packages for [Maslow OS](https://github.com/letsgomaslow/maslow-os). It is for contributors working on packaging, not for downloading an OS installer.

It is based on [Omarchy's package repository](https://github.com/omacom/omarchy-pkgs). Package names and update contracts stay compatible with the Omarchy engine.

## What this repo does

- Packages the Maslow desktop and its default settings.
- Packages the preinstalled AI tools, curated dock and launcher, and internal Chrome build.
- Defines package dependencies, contents, and ownership.
- Supplies packages to the [ISO builder](https://github.com/letsgomaslow/maslow-os-iso).

Recipes live in `pkgbuilds/<package>/PKGBUILD`, with supporting metadata in `.omarchy/package.json`.

## Platform and preview status

The current Maslow installer targets **x86_64 Intel/AMD PCs and virtual machines**, not just Apple computers. It has been tested on a Lenovo ThinkPad.

The inherited tooling includes ARM64 build support, but that does not mean Maslow has a supported ARM64 installer or complete ARM64 package set.

There is **no public signed Maslow package channel yet**. These recipes support internal preview builds. Publishing source code does not authorize distributing Chrome binaries, signing packages, or using upstream release infrastructure.

See the [native test record](https://github.com/letsgomaslow/maslow-os/blob/main/docs/handoffs/2026-09-05-verified-usb-native-acceptance.md) for exact tested commits and remaining checks.

## Working on packages

1. Read [AGENTS.md](AGENTS.md) and [DOWNSTREAM.md](DOWNSTREAM.md).
2. Use the `maslow` product branch. `master` is the upstream mirror.
3. Make the smallest change in the relevant recipe. Preserve upstream package names, plugin IDs, credits, and licenses.
4. Run the package checks, then validate affected packages through the sibling ISO builder using explicit source checkouts.

For local runtime packaging, `OMARCHY_SRC` selects the runtime checkout. Record its exact commit along with this repository's commit.

Run the focused packaging checks with Bash 5:

```bash
./test/maslow-packaging
```

Package changes still need their relevant build and installation checks. A source test alone does not prove an installed app works.

## Technical reference

The longer instructions for metadata, package builds, upstream sync, and inherited release tools are preserved in the [upstream infrastructure reference](docs/upstream-package-infrastructure.md). That page describes upstream behavior, not an approved Maslow publishing service.

Keep Maslow's temporary runtime update protection in place. Do not sign, publish, promote, or upload packages without separately approved Maslow infrastructure and keys.

## Related repositories

- [Maslow OS](https://github.com/letsgomaslow/maslow-os) — installed desktop and commands; branch `main`.
- [Maslow OS ISO](https://github.com/letsgomaslow/maslow-os-iso) — installer and test media; branch `maslow`.

See [NOTICE](NOTICE) for attribution and licensing information.
