"""Retire superseded staging candidates: archive the bytes, then relabel.

Spec: docs/specs/2026-09-15-staging-and-promotion.md section 5.

Staging holds at most one unpromoted version per package, so staging a new
one has to clear the old. Nothing here DELETES, for two reasons:

  * A failed candidate is evidence. "Why did the gate reject 2.18.0?" is not
    answerable once the artifact is gone, and that is exactly when it gets
    asked.
  * `anaconda remove` has no `--label` flag. It deletes from the repository,
    so `anaconda remove ga-fdp/<pkg>` removes every version including the
    ones users install from main. The first draft of the implementation plan
    contained that command.

So a retired candidate is downloaded, checksum-verified against what the API
says it should be, and only then MOVED to the attic label -- one atomic
relabel that both preserves it and clears staging. Two copies survive: the
archive directory (uploaded off-channel by the caller) and the attic label.

The guard and the verify-before-relabel are the safety properties of this
file. Do not edit either without re-running the tests that prove they fire.
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

OWNER = os.environ.get("ANACONDA_OWNER", "ga-fdp")
STAGING = os.environ.get("STAGING_LABEL", "staging")
PROTECTED = os.environ.get("PROTECTED_LABEL", "main")
ATTIC = os.environ.get("ATTIC_LABEL", "attic")
API = "https://api.anaconda.org"


def cli():
    """The anaconda-client executable, whichever name it is exposed under.

    The anaconda-client package declares only two console scripts, `binstar`
    and `conda-server`. The familiar `anaconda` command belongs to a
    DIFFERENT package, `anaconda-cli-base`, which anaconda-client depends on
    and plugs into. `pixi global install anaconda-client` therefore installs
    `anaconda` as a dependency but does not expose it, because pixi exposes
    the requested package's own binaries and not its dependencies'. A
    condax/pip install puts the whole tree on PATH, so `anaconda` is there.

    Both names run the same code and both accept upload/move/remove/label,
    so either will do -- but guessing one fails with "command not found",
    which reads as a credential problem and is not.
    """
    for name in ("binstar", "anaconda"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("neither `binstar` nor `anaconda` is on PATH. Install "
             "anaconda-client (pixi exposes it as `binstar`).")


class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Drop the token at the redirect hop.

    A download URL 302s to signed object storage. Forwarding an anaconda
    token there is both a 400 and a credential handed to a third party.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers = {k: v for k, v in new.headers.items()
                           if k.lower() != "authorization"}
            new.unredirected_hdrs.pop("Authorization", None)
        return new


_opener = urllib.request.build_opener(_StripAuthOnRedirect)


def _get(url, token):
    return urllib.request.Request(url, headers={"Authorization": "token " + token})


def files_for(package, token):
    """Every published file of a package, with its labels and checksums.

    Read from the REST API, never from repodata: repodata is CDN-cached and
    can lag, and acting on stale labels is how this touches the wrong thing.
    """
    try:
        payload = json.load(urllib.request.urlopen(
            _get(f"{API}/package/{OWNER}/{package}", token)))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []
        raise
    return payload.get("files", [])


def archive(record, into, token):
    """Download one file and prove it arrived intact. Returns its path."""
    blob = _opener.open(_get("https:" + record["download_url"], token)).read()

    actual, expected = hashlib.md5(blob).hexdigest(), record.get("md5")
    if expected and actual != expected:
        raise SystemExit(
            f"REFUSING to retire {record['full_name']}: downloaded bytes hash "
            f"{actual}, the channel says {expected}. The archive would not be "
            f"the artifact, so nothing is relabelled.")
    if len(blob) != record.get("size", len(blob)):
        raise SystemExit(
            f"REFUSING to retire {record['full_name']}: got {len(blob)} bytes, "
            f"expected {record['size']}.")

    into.mkdir(parents=True, exist_ok=True)
    path = into / record["basename"].split("/")[-1]
    path.write_bytes(blob)
    print(f"    archived {path.name} ({len(blob)} bytes, md5 {actual})")
    return path


def main(package, keep, archive_dir):
    token = os.environ.get("ANACONDA_API_TOKEN", "")
    if not token:
        sys.exit("ANACONDA_API_TOKEN is unset. Refusing to guess.")

    by_version = {}
    for f in files_for(package, token):
        by_version.setdefault(f["version"], []).append(f)
    if not by_version:
        print(f"{package}: not on the channel yet; nothing to retire")
        return 0

    for version, records in sorted(by_version.items()):
        labels = set().union(*(set(r.get("labels") or []) for r in records))
        if version == keep or STAGING not in labels:
            continue
        if PROTECTED in labels:
            print(f"REFUSING to retire {package} {version}: it is also on "
                  f"'{PROTECTED}'. Promotion moves rather than copies, so "
                  f"this state should be impossible -- investigate before "
                  f"retrying.", file=sys.stderr)
            return 1

        print(f"{package}: retiring superseded {version} from '{STAGING}'")
        for record in records:
            archive(record, pathlib.Path(archive_dir) / package / version, token)

        # Only now, with verified bytes on disk.
        subprocess.run([cli(), "-t", token, "move",
                        "--from-label", STAGING, "--to-label", ATTIC,
                        f"{OWNER}/{package}/{version}"], check=True)

        still = set().union(*(set(r.get("labels") or []) for r in
                              files_for(package, token)
                              if r["version"] == version)) or set()
        if STAGING in still:
            print(f"{package} {version} is still on '{STAGING}' after the "
                  f"move; staging now holds two versions and a later solve "
                  f"could take the wrong one.", file=sys.stderr)
            return 1
        print(f"    moved to '{ATTIC}'; labels now {sorted(still)}")

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: retire_staging.py <package> <version-being-staged> "
                 "<archive-dir>")
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
