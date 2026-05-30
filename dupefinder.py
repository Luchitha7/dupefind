#!/usr/bin/env python3
"""dupefind — find files with identical content and optionally remove copies.

Duplicates are detected in two passes: files are first grouped by size (a cheap
filter, since files of different sizes can't be identical), then each same-size
group is confirmed by SHA-256 hash. By default the tool only reports what it
finds; deletion is opt-in and always sends copies to the Trash.
"""

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
    """Return every regular file under *folder*, recursively."""
    files = []
    for path in Path(folder).rglob("*"):
        if path.is_file():
            files.append(path)
    return files


def group_by_size(files):
    """Group files by byte size, keeping only sizes shared by 2+ files."""
    sizes = defaultdict(list)
    for path in files:
        try:
            sizes[path.stat().st_size].append(path)
        except OSError as e:
            print(f"  skipping {path}: {e}", file=sys.stderr)
    return {size: paths for size, paths in sizes.items() if len(paths) > 1}


def hash_file(path, chunk_size=65536):
    """Return the SHA-256 hex digest of a file, read in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def group_by_hash(size_groups):
    """Confirm same-size files are identical by hashing, with progress.

    Files that can't be read are skipped with a warning so one bad file
    doesn't abort the whole run.
    """
    candidates = [path for paths in size_groups.values() for path in paths]
    hashes = defaultdict(list)

    iterator = candidates
    if tqdm is not None and candidates:
        iterator = tqdm(candidates, desc="Hashing", unit="file")

    for i, path in enumerate(iterator, 1):
        try:
            hashes[hash_file(path)].append(path)
        except OSError as e:
            print(f"  skipping {path}: {e}", file=sys.stderr)
        if tqdm is None and candidates:
            print(f"\rHashing {i}/{len(candidates)}", end="", file=sys.stderr)

    if tqdm is None and candidates:
        print(file=sys.stderr)  # newline after the manual counter

    return {h: paths for h, paths in hashes.items() if len(paths) > 1}


def report(dupe_groups):
    """Print the duplicate groups found (the default, read-only behavior)."""
    if not dupe_groups:
        print("No duplicates found.")
        return

    print(f"Found {len(dupe_groups)} group(s) of duplicates:\n")
    for i, paths in enumerate(dupe_groups.values(), 1):
        print(f"Group {i}:")
        for path in paths:
            print(f"  {path}")
        print()


def build_delete_plan(dupe_groups):
    """Choose one file to keep per group; return (keepers, to_delete).

    The first file in each group is kept and the rest are scheduled for
    removal, so every group always retains exactly one copy.
    """
    keepers = []
    to_delete = []
    for paths in dupe_groups.values():
        keepers.append(paths[0])
        to_delete.extend(paths[1:])
    return keepers, to_delete


def delete_duplicates(dupe_groups, dry_run=False):
    """Show the deletion plan and, on confirmation, send copies to Trash."""
    keepers, to_delete = build_delete_plan(dupe_groups)

    if not to_delete:
        print("No duplicates to delete.")
        return

    print(f"Found {len(dupe_groups)} group(s) of duplicates.")
    print(f"Will keep {len(keepers)} file(s) and remove {len(to_delete)} copy(ies):\n")
    for i, paths in enumerate(dupe_groups.values(), 1):
        print(f"Group {i}:")
        print(f"  KEEP   {paths[0]}")
        for path in paths[1:]:
            print(f"  DELETE {path}")
        print()

    if dry_run:
        print("Dry run: nothing was deleted.")
        return

    answer = input("Proceed with sending the above copies to Trash? Type 'y' to confirm: ")
    if answer.strip().lower() != "y":
        print("Aborted. Nothing was deleted.")
        return

    try:
        from send2trash import send2trash
    except ImportError:
        print(
            "Error: the 'send2trash' library is required for deletion.\n"
            "Install it with: pip install send2trash",
            file=sys.stderr,
        )
        sys.exit(1)

    removed = 0
    for path in to_delete:
        try:
            send2trash(str(path))
            print(f"  Trashed {path}")
            removed += 1
        except OSError as e:
            print(f"  Failed to trash {path}: {e}", file=sys.stderr)

    print(f"\nDone. Sent {removed} file(s) to Trash.")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="dupefind",
        description=(
            "Find files with identical content by grouping on size, then "
            "confirming with SHA-256 hashes. Reports duplicates by default; "
            "use --delete to move extra copies to the Trash (one copy per "
            "group is always kept)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("folder", help="folder to scan recursively for duplicates")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="send duplicate copies to the Trash (keeps one file per group); "
        "requires confirmation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="with --delete, print exactly what would be deleted without "
        "deleting anything",
    )
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

    if args.delete or args.dry_run:
        delete_duplicates(dupe_groups, dry_run=args.dry_run)
    else:
        report(dupe_groups)


if __name__ == "__main__":
    main()
