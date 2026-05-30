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

## Usage

```
python3 dupefinder.py <folder> [--delete] [--dry-run]
```

Run `python3 dupefinder.py --help` for the full option description.

The `<folder>` can be any path on your machine — relative or absolute. The scan
is always recursive (it includes every subfolder).

### 1. Report duplicates (default — deletes nothing)

```bash
python3 dupefinder.py ~/Downloads
```

### 2. Preview a deletion (dry run)

Shows exactly which files would be kept and which would be removed, without
touching anything:

```bash
python3 dupefinder.py ~/Downloads --delete --dry-run
```

### 3. Delete extra copies (sends to Trash)

Prints the plan, then asks for confirmation before sending the extra copies to
the Trash:

```bash
python3 dupefinder.py ~/Downloads --delete
```

### Tips

- Wrap paths that contain spaces in quotes: `"~/My Photos"`.
- To scan the folder you're currently in, use a dot: `python3 /path/to/dupefinder.py .`
- Running from outside the project? Give the full path to the script:
  `python3 /full/path/to/dupefinder.py ~/Downloads`
- To avoid typing the long path every time, add a shell alias:
  ```bash
  echo "alias dupefind='python3 /full/path/to/dupefinder.py'" >> ~/.zshrc
  source ~/.zshrc
  # then simply:
  dupefind ~/Downloads
  ```

## Sample output

Report mode:

```
$ python3 dupefinder.py testfolder
Hashing: 100%|██████████████████████████| 2/2 [00:00<00:00, 4200.00file/s]
Found 1 group(s) of duplicates:

Group 1:
  testfolder/a.txt
  testfolder/b.txt
```

Delete mode:

```
$ python3 dupefinder.py testfolder --delete
Hashing: 100%|██████████████████████████| 2/2 [00:00<00:00, 4100.00file/s]
Found 1 group(s) of duplicates.
Will keep 1 file(s) and remove 1 copy(ies):

Group 1:
  KEEP   testfolder/a.txt
  DELETE testfolder/b.txt

Proceed with sending the above copies to Trash? Type 'y' to confirm: y
  Trashed testfolder/b.txt

Done. Sent 1 file(s) to Trash.
```

## Troubleshooting

Common errors and how to fix them.

### `Error: <path> is not a directory.`

The folder path doesn't exist or is mistyped. Note that `~` expands to your
home folder, so `~/Test` means `/Users/you/Test`, **not** whatever folder your
terminal is currently sitting in.

- Check where you are with `pwd`, then pass that path.
- To scan the current folder, use a dot: `python3 dupefinder.py .`
- Quote paths with spaces: `python3 dupefinder.py "/Users/you/My Folder"`.

### `can't open file '.../dupefinder.py': [Errno 2] No such file or directory`

You pointed Python at the wrong script path (for example the literal
placeholder `/path/to/dupefind/`). Use the real, full path to the script, e.g.
`python3 /Users/you/Projects/dupefind/dupefinder.py ~/Downloads` — or `cd` into
the project folder first and just run `python3 dupefinder.py <folder>`.

### `ModuleNotFoundError: No module named 'send2trash'`  /  `the 'send2trash' library is required for deletion`

The deletion dependency isn't installed. Install the requirements:

```bash
python3 -m pip install -r requirements.txt
# or just the one library:
python3 -m pip install send2trash
```

Report mode and `--dry-run` work without it; only `--delete` needs it.

### `pip: command not found`

Use pip through Python instead of calling it directly:

```bash
python3 -m pip install -r requirements.txt
```

### `command not found: python3`

Python 3 isn't installed or isn't on your `PATH`. Install it from
[python.org](https://www.python.org/downloads/) (or via Homebrew on macOS:
`brew install python`), then re-open your terminal.

### `skipping <file>: [Errno 13] Permission denied`

This is **not** a crash — it's the safety guard. A file couldn't be read (locked
or owned by another user), so it was skipped and the scan continued. Re-run with
an account that can read the file if you need it included. Avoid running with
`sudo` just to force access unless you understand the consequences.

### No progress bar appears

`tqdm` isn't installed, so the tool falls back to a simple `Hashing N/M`
counter. Install it for the nicer bar: `python3 -m pip install tqdm`.

### I deleted the wrong file — can I get it back?

Yes. Deleted files are sent to your system **Trash / Recycle Bin**, not
permanently erased. Open the Trash and restore (on macOS: right-click →
"Put Back"). Use `--dry-run` first next time to preview the plan.
