# Google Chrome package provenance

This recipe is copied from the Arch User Repository `google-chrome` package at commit `b276fd5c9892f0902c21139c31edf75667a8620f` (`google-chrome 152.0.7977.82-1`). Automatic AUR synchronization is disabled so a future upstream update cannot enter a Maslow OS image without a new review and checksum verification.

The x86_64 package source is Google's official stable-channel Debian package at `https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_152.0.7977.82-1_amd64.deb`, verified by SHA-512 `867c023deb01fb838aa6a53291a617a9e18b8ff147a35c8b4af77956d633418544c49fadfd8e53a767d0a23a1f75e3b11e7ee32695c3242c24c65aa2b23791d7`.

`eula_text.html` is the upstream AUR package's copy of the Google Chrome custom license. The checked-in copy has one terminating newline added by repository tooling, and the local source checksum records that byte exactly.

This provenance review does not establish public redistribution rights for Google Chrome. The recipe is approved only for the explicitly authorized internal local-source test ISO; do not publish, upload, sign, or promote its package or an image containing it without separate legal and release approval.
