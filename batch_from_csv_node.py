"""
ComfyUI_Batch_from_CSV
A custom ComfyUI node for batch processing workflows from a CSV file.
Supports: prompts, two reference images (IMAGE), a video file path (STRING),
and a shot name (STRING) — all driven row-by-row via the seed widget.

CSV columns expected:
    positive      - positive prompt text
    negative      - negative prompt text
    ref_image_1   - Windows path to a .png reference image
    ref_image_2   - Windows path to a .png reference image
    video_file    - Windows path to a .mp4 video file
    shot_name     - string label used for output file naming
"""

import os
import csv
import re

import numpy as np
import torch
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv_dir() -> str:
    """Return the absolute path to the csv_files folder inside this node."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv_files")


def _list_csv_files() -> list[str]:
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
    ComfyUI-style IMAGE tensor  [1, H, W, 3]  float32 in [0, 1].
    Returns a 1×64×64 black image if the file is missing or unreadable.
    """
    norm = _normalise_path(path)
    if norm and os.path.isfile(norm):
        try:
            img = Image.open(norm).convert("RGB")
            arr = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(arr).unsqueeze(0)   # [1, H, W, 3]
        except Exception as e:
            print(f"[ComfyUI_Batch_from_CSV] WARNING: could not load image '{norm}': {e}")

    # Fallback — 64×64 black image so downstream nodes don't crash
    print(f"[ComfyUI_Batch_from_CSV] WARNING: image not found or unreadable: '{path}'. "
          "Returning blank placeholder.")
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


# ---------------------------------------------------------------------------
# Node class
# ---------------------------------------------------------------------------

class BatchFromCSV:
    """
    Reads one row per execution from a CSV file (selected by seed / batch counter).

    Outputs
    -------
    positive_string  STRING   – positive prompt
    negative_string  STRING   – negative prompt
    ref_image_1      IMAGE    – first reference image tensor
    ref_image_2      IMAGE    – second reference image tensor
    video_file       STRING   – normalised path to the video file
    shot_name        STRING   – shot / clip label for output file naming
    row_index        INT      – the actual row index that was loaded (useful for debugging)
    """

    CATEGORY = "Batch/CSV"
    FUNCTION = "load_row"
    RETURN_TYPES = ("STRING", "STRING", "IMAGE", "IMAGE", "STRING", "STRING", "INT")
    RETURN_NAMES = (
        "positive_string",
        "negative_string",
        "ref_image_1",
        "ref_image_2",
        "video_file",
        "shot_name",
        "row_index",
    )

    @classmethod
    def INPUT_TYPES(cls):
        csv_files = _list_csv_files()
        return {
            "required": {
                "csv_file": (csv_files, {"default": csv_files[0]}),
                "seed":     ("INT",     {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
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
            return ("", "", blank, blank, "", "", 0)

        row = _read_row(csv_file, seed)
        if not row:
            blank = torch.zeros(1, 64, 64, 3, dtype=torch.float32)
            return ("", "", blank, blank, "", "", seed)

        positive   = row.get("positive",    "").strip()
        negative   = row.get("negative",    "").strip()
        img1_path  = row.get("ref_image_1", "").strip()
        img2_path  = row.get("ref_image_2", "").strip()
        video_path = _normalise_path(row.get("video_file", ""))
        shot_name  = row.get("shot_name",   "").strip()

        row_index  = seed  # exposed so users can pipe it for debugging

        ref_image_1 = _load_image_as_tensor(img1_path)
        ref_image_2 = _load_image_as_tensor(img2_path)

        # Warn if video file is specified but missing
        if video_path and not os.path.isfile(video_path):
            print(f"[ComfyUI_Batch_from_CSV] WARNING: video file not found: '{video_path}'")

        print(
            f"[ComfyUI_Batch_from_CSV] Loaded row {seed}: "
            f"shot='{shot_name}' | video='{video_path}' | "
            f"img1='{img1_path}' | img2='{img2_path}'"
        )

        return (positive, negative, ref_image_1, ref_image_2, video_path, shot_name, row_index)


# ---------------------------------------------------------------------------
# ComfyUI registration
# ---------------------------------------------------------------------------

NODE_CLASS_MAPPINGS = {
    "BatchFromCSV": BatchFromCSV,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchFromCSV": "Batch from CSV 📋",
}
