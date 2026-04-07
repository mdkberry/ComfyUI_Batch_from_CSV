# ComfyUI_Batch_from_CSV 📋

A custom ComfyUI node for **batch/bulk workflow processing** driven entirely from a CSV file.  
Each row in the CSV represents one "shot" or generation job. The node reads one row per execution, making it perfect for automating large batches.

---

## ✨ Features

| Output connector | Type | Description |
|---|---|---|
| `positive_string` | STRING | Positive prompt text |
| `negative_string` | STRING | Negative prompt text |
| `ref_image_1` | IMAGE | First reference image loaded as a ComfyUI IMAGE tensor |
| `ref_image_2` | IMAGE | Second reference image loaded as a ComfyUI IMAGE tensor |
| `video_file` | STRING | Normalised path to your `.mp4` video file |
| `shot_name` | STRING | Label for the shot — use this to rename your output file |
| `row_index` | INT | The row number that was loaded (handy for debugging) |

- **Auto-scan** — any `.csv` file dropped in the `csv_files` folder is picked up automatically.
- **Seed-driven batching** — set seed to *increment* and queue N runs to process N rows.
- **Loop-safe** — if seed exceeds the number of rows the node wraps around.
- **Graceful fallback** — missing image files produce a blank 64×64 black tensor (no crash); missing video paths log a warning.
- **Windows paths supported** — backslashes are normalised automatically.

---

## 📥 Installation

### Manual (recommended)

1. Copy the `ComfyUI_Batch_from_CSV` folder into your ComfyUI `custom_nodes` directory:
   ```
   ComfyUI/custom_nodes/ComfyUI_Batch_from_CSV/
   ```
2. Restart ComfyUI.
3. The node appears under **Batch/CSV → Batch from CSV 📋**.

### Via ComfyUI Manager

1. Open **ComfyUI Manager → Install via Git URL**.
2. Paste your repository URL.
3. Restart ComfyUI.

---

## 📁 Folder Structure

```
ComfyUI/custom_nodes/ComfyUI_Batch_from_CSV/
│
├── csv_files/                  ← PUT YOUR CSV FILES HERE
│   ├── example_batch.csv
│   └── my_project.csv
│
├── __init__.py
├── batch_from_csv_node.py
├── pyproject.toml
└── README.md
```

---

## 📝 CSV Format

Your CSV must use these **exact column headers** (order doesn't matter):

| Column | Required | Description |
|---|---|---|
| `positive` | ✅ | Positive prompt text |
| `negative` | ✅ | Negative prompt text |
| `ref_image_1` | ✅ | Full Windows path to a `.png` reference image |
| `ref_image_2` | ✅ | Full Windows path to a second `.png` reference image |
| `video_file` | ✅ | Full Windows path to a `.mp4` video file |
| `shot_name` | ✅ | Name string used for output file renaming |

### Example CSV

```csv
positive,negative,ref_image_1,ref_image_2,video_file,shot_name
"A cinematic wide shot of a mountain","blurry, watermark","C:\refs\mountain1.png","C:\refs\mountain2.png","C:\videos\shot_001.mp4","shot_001_mountain"
"A portrait with dramatic lighting","distorted, ugly","C:\refs\portrait1.png","C:\refs\portrait2.png","C:\videos\shot_002.mp4","shot_002_portrait"
```

> **Tip:** Wrap cell values in double quotes if they contain commas.

---

## 🚀 How to Use (Batch Generation)

<img width="945" height="513" alt="csv-to-batch" src="https://github.com/user-attachments/assets/2aabf2f9-f9a1-4bf0-a69d-df31d04993a2" />



### Step 1 — Add the node

- Double-click the canvas → search for **"Batch from CSV"** (category: `Batch/CSV`).

### Step 2 — Select your CSV

- Choose your file from the `csv_file` dropdown.
- Click **Refresh** in the ComfyUI menu if a newly added file doesn't appear.

### Step 3 — Connect outputs

| Node output | Connect to |
|---|---|
| `positive_string` | CLIP Text Encode (Positive) → text |
| `negative_string` | CLIP Text Encode (Negative) → text |
| `ref_image_1` | Any node that accepts an IMAGE (e.g. IPAdapter, Load Image passthrough) |
| `ref_image_2` | Any node that accepts an IMAGE |
| `video_file` | Any node that accepts a STRING path (e.g. VHS Load Video → video path string) |
| `shot_name` | File naming / Save Image → filename_prefix |
| `row_index` | Optional — debug display or logging |

### Step 4 — Configure for batch

1. On the **Batch from CSV** node, set the `seed` widget control to **increment**.
2. In the ComfyUI menu set **Batch count** to the number of rows in your CSV.
3. Click **Queue Prompt** — ComfyUI will run once per row, automatically loading the next row each time.

---

## ❓ Troubleshooting

| Problem | Fix |
|---|---|
| No CSV files in dropdown | Make sure your `.csv` is inside the `csv_files` folder, then click **Refresh** |
| Image outputs are blank/black | Check the path in the CSV is correct and the file exists |
| Video path warning in console | The path is returned as a string even if missing — check spelling |
| Row not advancing | Ensure the seed is set to **increment**, not fixed |

---

## Credits

This work was based on and inspired by https://github.com/TharindaMarasingha/ComfyUI-CSV-to-Prompt

## 📄 License

MIT — free to use, modify, and share.

