"""Build the archived Linux microbenchmark; timing is a separate operation."""
import os
import argparse
import hashlib
import tomllib
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--prepare-only", action="store_true", help="verify and prepare sources without compiling")
args = parser.parse_args()
archive = Path(__file__).resolve().parent
root = Path(os.environ.get("VELLO_BENCH_ROOT", str(archive / "replay")))
root.mkdir(parents=True, exist_ok=True)
crate = root / "vello_cpu-0.4.0.crate"
if not crate.exists():
    urllib.request.urlretrieve(
        "https://static.crates.io/crates/vello_cpu/vello_cpu-0.4.0.crate", crate
    )
lock = tomllib.loads((archive / "harness/unpack-bench-original/Cargo.lock").read_text())
expected = next(p["checksum"] for p in lock["package"]
                if p["name"] == "vello_cpu" and p["version"] == "0.4.0")
actual = hashlib.sha256(crate.read_bytes()).hexdigest()
if actual != expected:
    raise RuntimeError(f"crate checksum mismatch: {actual} != {expected}")
original = root / "vello_cpu-0.4.0"
if not original.exists():
    with tarfile.open(crate) as contents:
        contents.extractall(root, filter="data")
for variant, directory in [
    ("loop", "vello_cpu-0.4.0-before-bytes-of"),
    ("bytes", "vello_cpu-0.4.0-pod"),
]:
    destination = root / directory
    if not destination.exists():
        shutil.copytree(original, destination)
        subprocess.run(
            ["patch", "-p1", "-i", str(archive / "patches" / f"{variant}.patch")],
            cwd=destination, stdin=subprocess.DEVNULL, check=True,
        )
env = dict(os.environ)
env["CARGO_TARGET_DIR"] = str(root / "native-target")
env["CARGO_INCREMENTAL"] = "0"
for variant in ["original", "loop", "bytes"]:
    directory = f"unpack-bench-{variant}"
    shutil.copytree(archive / "harness" / directory, root / directory, dirs_exist_ok=True)
    # Each replay package is independent of the enclosing Vello workspace.
    manifest = root / directory / "Cargo.toml"
    manifest.write_text(manifest.read_text() + "\n[workspace]\n")
    if not args.prepare_only:
        subprocess.run(
            ["cargo", "+1.99.1", "build", "--locked", "--release", "--manifest-path",
             str(root / directory / "Cargo.toml")], env=env, check=True,
        )
