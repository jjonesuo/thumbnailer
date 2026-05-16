# YouTube Thumbnailer

`thumbnailer.py` is a Python script that scans a directory for video files containing YouTube video IDs in their filenames, downloads the highest-quality thumbnail using `yt-dlp`, converts it to a standard JPEG using `ffmpeg`, and saves it alongside the original video.

## Features

- **Automated ID Detection**: Automatically extracts 11-character YouTube IDs from filenames.
- **High-Quality Thumbnails**: Leverages `yt-dlp` to fetch the best available thumbnail image.
- **Standardized Output**: Converts images (WebP, PNG, etc.) to JPEG format using `ffmpeg`.
- **Flexible Scanning**: Supports recursive directory scanning and dry-run modes.
- **Smart Skipping**: Skips files that already have a poster unless forced to re-download.

## Prerequisites

Before using this script, ensure you have the following installed:

1.  **Python 3.6+**
2.  **yt-dlp**: Used to fetch thumbnail URLs and metadata.
    ```bash
    pip install yt-dlp
    ```
3.  **ffmpeg**: Used for image format conversion.
    - **Linux**: `sudo apt install ffmpeg`
    - **macOS**: `brew install ffmpeg`
    - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Installation

Simply download or clone this repository and ensure `thumbnailer.py` is executable:

```bash
chmod +x thumbnailer.py
```

## Usage

Run the script by providing a directory path (defaults to the current directory).

```bash
python3 thumbnailer.py [OPTIONS] [DIRECTORY]
```

### Options

| Option | Long Form | Description |
| :--- | :--- | :--- |
| `-r` | `--recursive` | Scan subdirectories recursively. |
| `-n` | `--dry-run` | Preview which IDs would be processed without downloading. |
| `-f` | `--force` | Re-download thumbnails even if `-poster.jpg` exists. |
| `-v` | `--verbose` | Show full output from `yt-dlp` and `ffmpeg`. |

### Examples

```bash
# Scan the current directory
python3 thumbnailer.py

# Scan a specific directory recursively
python3 thumbnailer.py -r ~/Videos/YouTube

# Perform a dry run to see what would happen
python3 thumbnailer.py -n .

# Force re-downloading of all posters in the current folder
python3 thumbnailer.py -f
```

## How it works

### YouTube ID Detection

The script looks for an 11-character YouTube ID in the filename using two primary methods:

1.  **Bracketed Format**: The default `yt-dlp` format, e.g., `My Video [dQw4w9WgXcQ].mp4`.
2.  **Trailing ID**: An ID at the end of the filename stem, preceded by a separator (hyphen, underscore, space, etc.), e.g., `my-video-dQw4w9WgXcQ.mkv`.

### File Naming

The resulting thumbnail is saved using the original filename's stem appended with `-poster.jpg`.

- **Input**: `Cool_Vlog_[abc12345678].mp4`
- **Output**: `Cool_Vlog_[abc12345678]-poster.jpg`

## License

This project is open-source and available under the MIT License.
