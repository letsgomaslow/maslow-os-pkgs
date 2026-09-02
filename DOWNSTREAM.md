# Maslow OS package downstream

This repository is the package-build downstream for Maslow OS, based on
`omacom/omarchy-pkgs`.

## Branch policy

- `master` is a fast-forward-only mirror of upstream `master`.
- `maslow` is the public product branch. It is never rebased after publication.
- Upstream changes reach `maslow` through reviewed merge commits or pull requests.

## Preview scope

Only `omarchy-dev` and `omarchy-settings-dev` source the Maslow OS `maslow`
branch during the preview milestone. Their package names, dependencies, internal
paths, and service identifiers remain compatible with Omarchy.

The runtime package owns `/usr/share/omarchy/maslow-version` alongside the independent Omarchy engine version at `/usr/share/omarchy/version`. The settings package installs Maslow branding, canonical metadata under `/usr/share/maslow-os`, Manrope and its OFL license, and a branded `/etc/os-release`.

No package from this branch is a signed public release. Publishing requires
Maslow-owned signing keys, a package repository, mirrors, checksums, release
automation, an update channel, and a validated rollback procedure.

## Upstream sync

1. Fetch `upstream` and fast-forward local `master` to `upstream/master`.
2. Push the mirrored `master` without force.
3. Merge `master` into `maslow` in a review branch.
4. Run repository self-tests and `./test/maslow-packaging` in Linux.
5. Review and merge without rewriting public history.
