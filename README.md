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

## Safety guarantees

- **Report-only by default.** Running without `--delete` only prints what it
  finds. Nothing is ever touched.
- **Always keeps one copy.** Within each duplicate group, one file is kept and
  only the *extra* copies are removed.
- **Trash, not permanent deletion.** Removed files are sent to the system
  Trash / Recycle Bin via [`send2trash`](https://github.com/arsenetar/send2trash).
  The tool never hard-deletes with `os.remove`, so anything removed can be
  restored.
- **Explicit confirmation.** Before deleting, the full plan is printed and you
  must type `y` to proceed.
- **`--dry-run`** lets you preview the exact deletion plan without removing
  anything.
- **Resilient.** A single unreadable file is skipped with a warning instead of
  crashing the whole run.

## Requirements

- Python 3.8 or newer
- [`send2trash`](https://github.com/arsenetar/send2trash) — required for `--delete`
- [`tqdm`](https://github.com/tqdm/tqdm) — progress bar (optional; the tool
  falls back to a plain counter if it isn't installed)

## Installation

```bash
# 1. get the code
git clone https://github.com/Luchitha7/dupefind.git
cd dupefind

# 2. (optional but recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. install dependencies
python3 -m pip install -r requirements.txt
```
