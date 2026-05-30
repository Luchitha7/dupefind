import sys
import hashlib
from pathlib import Path
from collections import defaultdict


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
    hashes = defaultdict(list)
    for paths in size_groups.values():
        for path in paths:
            try:
                hashes[hash_file(path)].append(path)
            except OSError:
                pass
    return {h: paths for h, paths in hashes.items() if len(paths) > 1}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dupefinder.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]
    files = get_all_files(folder)
    size_groups = group_by_size(files)
    dupe_groups = group_by_hash(size_groups)

    if not dupe_groups:
        print("No duplicates found.")
        return

    print(f"Found {len(dupe_groups)} group(s) of duplicates:\n")
    for i, paths in enumerate(dupe_groups.values(), 1):
        print(f"Group {i}:")
        for path in paths:
            print(f"  {path}")
        print()


if __name__ == "__main__":
    main()
