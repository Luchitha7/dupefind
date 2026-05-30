import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:  # progress bar is a nicety, not a hard requirement
    tqdm = None


def get_all_files(folder):
    files = []
    for path in Path(folder).rglob("*"):
        if path.is_file():
            files.append(path)
    return files


def group_by_size(files):
    sizes = defaultdict(list)
    for path in files:
        try:
            sizes[path.stat().st_size].append(path)
        except OSError:
            pass
    return {size: paths for size, paths in sizes.items() if len(paths) > 1}


def hash_file(path, chunk_size=65536):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def group_by_hash(size_groups):
    candidates = [path for paths in size_groups.values() for path in paths]
    hashes = defaultdict(list)

    iterator = candidates
    if tqdm is not None and candidates:
        iterator = tqdm(candidates, desc="Hashing", unit="file")

    for i, path in enumerate(iterator, 1):
        try:
            hashes[hash_file(path)].append(path)
        except OSError:
            pass
        if tqdm is None and candidates:
            print(f"\rHashing {i}/{len(candidates)}", end="", file=sys.stderr)

    if tqdm is None and candidates:
        print(file=sys.stderr)

    return {h: paths for h, paths in hashes.items() if len(paths) > 1}


def report(dupe_groups):
    if not dupe_groups:
        print("No duplicates found.")
        return

    print(f"Found {len(dupe_groups)} group(s) of duplicates:\n")
    for i, paths in enumerate(dupe_groups.values(), 1):
        print(f"Group {i}:")
        for path in paths:
            print(f"  {path}")
        print()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="dupefind",
        description=(
            "Find files with identical content by grouping on size, then "
            "confirming with SHA-256 hashes."
        ),
    )
    parser.add_argument("folder", help="folder to scan recursively for duplicates")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory.", file=sys.stderr)
        sys.exit(1)

    files = get_all_files(folder)
    size_groups = group_by_size(files)
    dupe_groups = group_by_hash(size_groups)
    report(dupe_groups)


if __name__ == "__main__":
    main()
