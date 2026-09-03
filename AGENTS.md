# Maslow OS Package Repository Agent Instructions

Work in this repository as part of the three-repository Maslow OS product pipeline. Optimize for correct package contents, reproducible ownership, and compatibility with upstream Omarchy.

# Repository Role

This repository owns Arch package recipes and package infrastructure. It does not own the Maslow desktop source or the ISO installer.

- `letsgomaslow/maslow-os` owns the installed runtime and visible product experience. Its public product branch is `main`.
- `letsgomaslow/maslow-os-pkgs` (this repository) turns that source into compatible Arch packages. Its downstream product branch is `maslow`; `master` mirrors upstream.
- `letsgomaslow/maslow-os-iso` consumes this repository together with the runtime source to build bootable x86_64 installation media. Its downstream product branch is `maslow`.

The dependency flow is `maslow-os source` -> `maslow-os-pkgs package recipes` -> `maslow-os-iso installation media`.

# Change Routing

- Change `PKGBUILD` files, package metadata, dependencies, file ownership, install hooks, and publication helpers here.
- Change desktop commands, themes, product UI, runtime defaults, migrations, and end-user documentation in `maslow-os`.
- Change installer screens, boot media, live-environment packages, offline-mirror assembly, and VM orchestration in `maslow-os-iso`.
- Do not duplicate runtime files here when the package should copy them from the source checkout.

# Source and Branch Rules

- Never assume sibling repositories share this repository's default branch. Inspect each downstream remote.
- Maslow package recipes that fetch product source must track `https://github.com/letsgomaslow/maslow-os.git#branch=main`.
- Local and ISO builds should pass `OMARCHY_SRC` to package an explicit source checkout. Record the exact source and package commits used for release evidence.
- Preserve the established Omarchy package names, `provides`, `conflicts`, internal paths, commands, and service identifiers unless a separately approved compatibility migration exists.
- During the preview milestone, `omarchy-dev` and `omarchy-settings-dev` are local-source validation packages, not proof of a public stable channel.
- Do not sign, publish, promote, or upload packages until Maslow-owned release infrastructure and keys are explicitly approved.

# Working Style

- Inspect the relevant recipe, its `.omarchy` metadata, and any install hook before editing.
- Make the smallest coherent change and keep unrelated upstream packaging behavior intact.
- Use Bash 5 syntax, two-space indentation, and `[[ ]]` or `(( ))` for tests.
- Do not force-push or rebase the public `maslow` branch.
- Keep commits atomic and use reviewed pull requests for downstream changes.

# Verification

- Run `git diff --check`.
- Run `./test/maslow-packaging` for Maslow-owned package invariants.
- Run focused syntax or package-build checks for every recipe changed.
- For file-ownership changes, build the affected packages together and run the ISO repository's overlap check before claiming success.
- A release candidate is not complete until the sibling ISO repository builds from the exact runtime and package commits and completes a fresh VM installation.
