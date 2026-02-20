#!/usr/bin/env python3
"""
thumbnailer - Download YouTube thumbnails for video files whose names contain a YouTube ID.

For each video file found, the script:
  1. Extracts the YouTube video ID from the filename
  2. Downloads the best available thumbnail using yt-dlp
  3. Converts it to JPEG using ffmpeg
  4. Saves it as <original-stem>-poster.jpg next to the video file

YouTube ID detection:
  - [VIDEO_ID] bracket format  (yt-dlp default, e.g. "My Video [dQw4w9WgXcQ].mp4")
  - Trailing ID after a separator (e.g. "my-video-dQw4w9WgXcQ.mkv")

Usage:
  python thumbnailer.py [OPTIONS] [DIRECTORY]

Options:
  -r, --recursive      Scan subdirectories recursively
  -n, --dry-run        Print what would be done without downloading
  --skip-existing      Skip files that already have a -poster.jpg alongside them
  -v, --verbose        Show full yt-dlp and ffmpeg output
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
    ".webm", ".m4v", ".ts", ".m2ts", ".3gp", ".ogv",
}

# Primary: yt-dlp default format  →  Title [dQw4w9WgXcQ].mp4
_BRACKETED_RE = re.compile(r"\[([a-zA-Z0-9_-]{11})\]")

# Fallback: ID at the very end of the stem, preceded by a non-word character
_TRAILING_RE = re.compile(r"(?:^|[-_. (])([a-zA-Z0-9_-]{11})$")


def extract_youtube_id(filename: str) -> Optional[str]:
    stem = Path(filename).stem

    m = _BRACKETED_RE.search(stem)
    if m:
        return m.group(1)

    m = _TRAILING_RE.search(stem)
    if m:
        return m.group(1)

    return None


def download_thumbnail(video_id: str, output_path: Path, verbose: bool = False) -> bool:
    """Download the thumbnail for *video_id* and write a JPEG to *output_path*.

    Returns True on success, False on failure.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use a fixed basename so we can reliably find the file afterwards.
        # yt-dlp appends the thumbnail format extension (e.g. .webp, .jpg).
        output_template = os.path.join(tmpdir, "thumb")

        yt_cmd = [
            "yt-dlp",
            "--write-thumbnail",
            "--skip-download",
            "--no-playlist",
            "-o", output_template,
            url,
        ]

        capture = not verbose
        yt_result = subprocess.run(
            yt_cmd,
            capture_output=capture,
            text=True,
        )

        # Discover whatever yt-dlp wrote (name may vary by version / thumbnail format)
        candidates = [f for f in Path(tmpdir).iterdir() if f.is_file()]

        if not candidates:
            print(f"    [yt-dlp] No thumbnail file written.")
            if capture and yt_result.stderr.strip():
                for line in yt_result.stderr.strip().splitlines():
                    print(f"    [yt-dlp] {line}")
            return False

        thumb_file = candidates[0]

        # Convert to JPEG with ffmpeg
        ff_cmd = [
            "ffmpeg",
            "-y",               # overwrite output without asking
            "-i", str(thumb_file),
            str(output_path),
        ]

        ff_result = subprocess.run(
            ff_cmd,
            capture_output=capture,
            text=True,
        )

        if ff_result.returncode != 0:
            print(f"    [ffmpeg] Conversion failed (exit {ff_result.returncode})")
            if capture and ff_result.stderr.strip():
                # Print only the last few lines to avoid flooding the console
                tail = ff_result.stderr.strip().splitlines()[-5:]
                for line in tail:
                    print(f"    [ffmpeg] {line}")
            return False

        return True


def scan_directory(
    directory: Path,
    recursive: bool,
    dry_run: bool,
    skip_existing: bool,
    verbose: bool,
) -> None:
    pattern = "**/*" if recursive else "*"
    video_files = sorted(
        f
        for f in directory.glob(pattern)
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not video_files:
        print("No video files found.")
        return

    print(f"Found {len(video_files)} video file(s).\n")

    processed = skipped = failed = 0

    for video_file in video_files:
        video_id = extract_youtube_id(video_file.name)

        if not video_id:
            print(f"  SKIP  {video_file.name}")
            print(f"        Reason : no YouTube ID detected in filename")
            skipped += 1
            print()
            continue

        poster_path = video_file.parent / (video_file.stem + "-poster.jpg")

        if skip_existing and poster_path.exists():
            print(f"  SKIP  {video_file.name}")
            print(f"        Reason : poster already exists ({poster_path.name})")
            skipped += 1
            print()
            continue

        print(f"  PROC  {video_file.name}")
        print(f"        ID     : {video_id}")
        print(f"        Output : {poster_path}")

        if dry_run:
            print(f"        [dry run — skipping download]")
            skipped += 1
            print()
            continue

        success = download_thumbnail(video_id, poster_path, verbose=verbose)

        if success:
            print(f"        Status : OK")
            processed += 1
        else:
            print(f"        Status : FAILED")
            failed += 1

        print()

    summary = f"Done.  Processed: {processed}  Skipped: {skipped}  Failed: {failed}"
    print("-" * len(summary))
    print(summary)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a directory for video files whose filenames contain a YouTube video ID, "
            "download the corresponding thumbnail via yt-dlp, convert it to JPEG via ffmpeg, "
            "and save it as <videoname>-poster.jpg next to the original file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  thumbnailer.py                        # scan current directory\n"
            "  thumbnailer.py ~/Videos               # scan ~/Videos\n"
            "  thumbnailer.py -r ~/Videos            # scan recursively\n"
            "  thumbnailer.py -n ~/Videos            # dry run\n"
            "  thumbnailer.py --skip-existing ~/Videos\n"
        ),
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Scan subdirectories recursively",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be done without downloading anything",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip video files that already have a -poster.jpg alongside them",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show full yt-dlp and ffmpeg output",
    )

    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    scan_directory(
        directory=directory,
        recursive=args.recursive,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
