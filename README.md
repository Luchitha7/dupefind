# dupefind

A small command-line tool that finds files with **identical content** in a
folder (and its subfolders) and, optionally, cleans up the extra copies by
sending them to your system Trash.

## How it works

Comparing every file against every other file byte-for-byte would be slow, so
`dupefind` works in two passes:

1. **Group by size** — files of different sizes can't be identical, so files
   are first bucketed by their byte size. Any size shared by only one file is
   discarded immediately.
2. **Confirm by hash** — the remaining same-size candidates are read and hashed
   with **SHA-256**. Files whose hashes match are genuine content duplicates.

A progress bar (via [`tqdm`](https://github.com/tqdm/tqdm)) is shown during the
hashing pass so large folders don't look frozen.
