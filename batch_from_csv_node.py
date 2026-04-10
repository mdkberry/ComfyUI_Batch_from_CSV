"""
ComfyUI_Batch_from_CSV

A custom ComfyUI node for batch processing workflows from a CSV file.

Supports: prompts, three reference images (IMAGE), a video file path (STRING),
a shot name (STRING), and a full-row info string (STRING) — all driven
row-by-row via the seed widget.

CSV columns expected:
    positive    - positive prompt text
    negative    - negative prompt text
    ref_image_1 - Windows path to a .png reference image
    ref_image_2 - Windows path to a .png reference image
    ref_image_3 - Windows path to a .png reference image
    video_file  - Windows path to a .mp4 video file
    shot_name   - string label used for output file naming
"""

import os
import csv
import numpy as np
import torch
from PIL import Image

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv_dir() -> str:
    """Return the absolute path to the csv_files folder inside this node."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv_files")


def _list_csv_files() -> list:
    """Return a sorted list of CSV filenames found in csv_files/."""
    d = _csv_dir()
    if not os.path.isdir(d):
        return ["No CSV files found"]
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(".csv"))
    return files if files else ["No CSV files found"]


def _normalise_path(raw: str) -> str:
    """
    Convert a Windows-style path (with backslashes) to whatever the OS needs.
    Works transparently on both Windows and Linux.
    """
    return os.path.normpath(raw.strip()) if raw and raw.strip() else ""


def _load_image_as_tensor(path: str):
    """
    Load a PNG (or any PIL-supported image) from *path* and return it as a
    ComfyUI-style IMAGE tensor [1, H, W, 3] float32 in [0, 1].

    Returns a 1×64×64 black image if the file is missing or unreadable.
    """
    norm = _normalise_path(path)
    if norm and os.path.isfile(norm):
        try:
            img = Image.open(norm).convert("RGB")
            arr = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(arr).unsqueeze(0)  # [1, H, W, 3]
        except Exception as e:
            print(f"[ComfyUI_Batch_from_CSV] WARNING: could not load image '{norm}': {e}")

    # Fallback — 64×64 black image so downstream nodes don't crash
    print(
        f"[ComfyUI_Batch_from_CSV] WARNING: image not found or unreadable: '{path}'. "
        "Returning blank placeholder."
    )
    arr = np.zeros((64, 64, 3), dtype=np.float32)
    return torch.from_numpy(arr).unsqueeze(0)


def _read_row(csv_filename: str, row_index: int) -> dict:
    """
    Read a single row (0-based index) from the given CSV file.
    Returns a dict keyed by column name.
    """
    filepath = os.path.join(_csv_dir(), csv_filename)
    if not os.path.isfile(filepath):
        print(f"[ComfyUI_Batch_from_CSV] ERROR: CSV file not found: {filepath}")
        return {}

    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    if not rows:
        print(f"[ComfyUI_Batch_from_CSV] WARNING: CSV file is empty: {filepath}")
        return {}

    # Wrap around so the node loops cleanly when seed > number of rows
    idx = row_index % len(rows)
    return rows[idx]


def _build_info_string(row: dict, row_index: int, csv_filename: str) -> str:
    """
    Build a human-readable summary of the entire row to pipe into a Show Any node.
    This gets embedded in the PNG workflow metadata so you can inspect it later.
    """
    lines = [
        f"=== Batch from CSV — Row {row_index} ({csv_filename}) ===",
        f"shot_name  : {row.get('shot_name', '').strip()}",
        f"positive   : {row.get('positive', '').strip()}",
        f"negative   : {row.get('negative', '').strip()}",
        f"ref_image_1: {row.get('ref_image_1', '').strip()}",
        f"ref_image_2: {row.get('ref_image_2', '').strip()}",
        f"ref_image_3: {row.get('ref_image_3', '').strip()}",
        f"video_file : {row.get('video_file', '').strip()}",
    ]
    # Append any extra columns that may exist in the CSV but aren't listed above
    known_keys = {"shot_name", "positive", "negative",
                  "ref_image_1", "ref_image_2", "ref_image_3", "video_file"}
    for key, value in row.items():
        if key not in known_keys:
            lines.append(f"{key:<11}: {str(value).strip()}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node class
# ---------------------------------------------------------------------------

class BatchFromCSV:
    """
    Reads one row per execution from a CSV file (selected by seed / batch counter).

    Outputs
    -------
    positive_string  STRING  – positive prompt
    negative_string  STRING  – negative prompt
    ref_image_1      IMAGE   – first reference image tensor
    ref_image_2      IMAGE   – second reference image tensor
    ref_image_3      IMAGE   – third reference image tensor
    video_file       STRING  – normalised path to the video file
    shot_name        STRING  – shot / clip label for output file naming
    row_index        INT     – the actual row index that was loaded (useful for debugging)
    info             STRING  – full row summary for Show Any node / PNG metadata
    """

    CATEGORY = "Batch/CSV"
    FUNCTION = "load_row"

    RETURN_TYPES = ("STRING", "STRING", "IMAGE", "IMAGE", "IMAGE", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = (
        "positive_string",
        "negative_string",
        "ref_image_1",
        "ref_image_2",
        "ref_image_3",
        "video_file",
        "shot_name",
        "row_index",
        "info",
    )

    @classmethod
    def INPUT_TYPES(cls):
        csv_files = _list_csv_files()
        return {
            "required": {
                "csv_file": (csv_files, {"default": csv_files[0]}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            }
        }

    # Tell ComfyUI this node is NOT purely deterministic (seed changes output)
    @classmethod
    def IS_CHANGED(cls, csv_file, seed):
        return float(seed)

    def load_row(self, csv_file: str, seed: int):
        if csv_file == "No CSV files found":
            print("[ComfyUI_Batch_from_CSV] ERROR: No CSV file selected or available.")
            blank = torch.zeros(1, 64, 64, 3, dtype=torch.float32)
            return ("", "", blank, blank, blank, "", "", 0, "No CSV file selected.")

        row = _read_row(csv_file, seed)
        if not row:
            blank = torch.zeros(1, 64, 64, 3, dtype=torch.float32)
            return ("", "", blank, blank, blank, "", "", seed, "Empty or unreadable CSV row.")

        positive   = row.get("positive",    "").strip()
        negative   = row.get("negative",    "").strip()
        img1_path  = row.get("ref_image_1", "").strip()
        img2_path  = row.get("ref_image_2", "").strip()
        img3_path  = row.get("ref_image_3", "").strip()
        video_path = _normalise_path(row.get("video_file", ""))
        shot_name  = row.get("shot_name",   "").strip()
        row_index  = seed  # exposed so users can pipe it for debugging

        ref_image_1 = _load_image_as_tensor(img1_path)
        ref_image_2 = _load_image_as_tensor(img2_path)
        ref_image_3 = _load_image_as_tensor(img3_path)

        # Warn if video file is specified but missing
        if video_path and not os.path.isfile(video_path):
            print(f"[ComfyUI_Batch_from_CSV] WARNING: video file not found: '{video_path}'")

        info = _build_info_string(row, seed, csv_file)

        print(
            f"[ComfyUI_Batch_from_CSV] Loaded row {seed}: "
            f"shot='{shot_name}' | video='{video_path}' | "
            f"img1='{img1_path}' | img2='{img2_path}' | img3='{img3_path}'"
        )

        return (
            positive,
            negative,
            ref_image_1,
            ref_image_2,
            ref_image_3,
            video_path,
            shot_name,
            row_index,
            info,
        )


# ---------------------------------------------------------------------------
# ComfyUI registration
# ---------------------------------------------------------------------------

NODE_CLASS_MAPPINGS = {
    "BatchFromCSV": BatchFromCSV,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchFromCSV": "Batch from CSV 📋",
}
