# ComfyUI_Batch_from_CSV 📋

***THIS IS IN THE PROCESS OF BEING UPDATED AND RENAMED. RECOMMENDED NOT TO INSTALL AT THIS TIME UNTIL THAT HAS HAPPENED***

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
| `ref_image_3` | IMAGE | Third reference image loaded as a ComfyUI IMAGE tensor |
| `video_file` | STRING | Normalised path to your `.mp4` video file |
| `shot_name` | STRING | Label for the shot — use this to rename your output file |
| `row_index` | INT | The row number that was loaded (handy for debugging) |
| `info` | STRING | Full row summary — pipe into a **Show Any** node to embed all row data in your PNG workflow metadata |

* **Auto-scan** — any `.csv` file dropped in the `csv_files` folder is picked up automatically.
* **Seed-driven batching** — set seed to *increment* and queue N runs to process N rows.
* **Loop-safe** — if seed exceeds the number of rows the node wraps around.
* **Graceful fallback** — missing image files produce a blank 64×64 black tensor (no crash); missing video paths log a warning.
* **Windows paths supported** — backslashes are normalised automatically.

---

## 📥 Installation

### Manual (recommended)

1. CD into your ComfyUI `custom_nodes` directory:
   ```
   ComfyUI/custom_nodes/
   ```
2. Install from command prompt in that folder using 
```
git clone https://github.com/mdkberry/ComfyUI_Batch_from_CSV
```
4. Restart ComfyUI.
5. The node appears under **Batch/CSV → Batch from CSV 📋**.

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
| `ref_image_1` | ✅ | Full path to a `.png` reference image |
| `ref_image_2` | ✅ | Full path to a second `.png` reference image |
| `ref_image_3` | ✅ | Full path to a third `.png` reference image |
| `video_file` | ✅ | Full path to a `.mp4` video file |
| `shot_name` | ✅ | Name string used for output file renaming |

> **Note:** `ref_image_3` is optional in the sense that if left blank or absent the node returns a blank 64×64 black tensor — no crash.

### Example CSV

```
positive,negative,ref_image_1,ref_image_2,ref_image_3,video_file,shot_name
"A cinematic wide shot of a mountain","blurry, watermark","C:\refs\mountain1.png","C:\refs\mountain2.png","C:\refs\mountain3.png","C:\videos\shot_001.mp4","shot_001_mountain"
"A portrait with dramatic lighting","distorted, ugly","C:\refs\portrait1.png","C:\refs\portrait2.png","C:\refs\portrait3.png","C:\videos\shot_002.mp4","shot_002_portrait"
```

> **Tip:** Wrap cell values in double quotes if they contain commas.

---

## 🚀 How to Use (Batch Generation)

### Step 1 — Add the node

* Double-click the canvas → search for **"Batch from CSV"** (category: `Batch/CSV`).

### Step 2 — Select your CSV

* Choose your file from the `csv_file` dropdown.
* Click **Refresh** in the ComfyUI menu if a newly added file doesn't appear.

### Step 3 — Connect outputs

| Node output | Connect to |
|---|---|
| `positive_string` | CLIP Text Encode (Positive) → text |
| `negative_string` | CLIP Text Encode (Negative) → text |
| `ref_image_1` | Any node that accepts an IMAGE (e.g. IPAdapter, Load Image passthrough) |
| `ref_image_2` | Any node that accepts an IMAGE |
| `ref_image_3` | Any node that accepts an IMAGE |
| `video_file` | Any node that accepts a STRING path (e.g. VHS Load Video → video path string) |
| `shot_name` | File naming / Save Image → filename_prefix |
| `row_index` | Optional — debug display or logging |
| `info` | **Show Any** (easy-use) node — embeds full row data in PNG workflow metadata |

### Step 4 — Connect the `info` output to Show Any

The `info` output produces a formatted text block like this for every run:

```
=== Batch from CSV — Row 0 (my_batch.csv) ===
shot_name  : shot_001_mountain
positive   : A cinematic wide shot of a mountain
negative   : blurry, watermark
ref_image_1: C:\refs\mountain1.png
ref_image_2: C:\refs\mountain2.png
ref_image_3: C:\refs\mountain3.png
video_file : C:\videos\shot_001.mp4
```

Plug this into a **Show Any** node (from ComfyUI easy-use). Because Show Any stores its value in the PNG workflow metadata, you can reload any generated image into ComfyUI later and immediately see every input that produced it — prompts, image paths, and video path all in one place.

### Step 5 — Configure for batch

1. On the **Batch from CSV** node, set the `seed` widget control to **increment**.
2. In the ComfyUI menu set **Batch count** to the number of rows in your CSV.
3. Click **Queue Prompt** — ComfyUI will run once per row, automatically loading the next row each time.

---

## ❓ Troubleshooting

| Problem | Fix |
|---|---|
| No CSV files in dropdown | Make sure your `.csv` is inside the `csv_files` folder, then click **Refresh** or press `R` to reload nodes inside comfyUI |
| Image outputs are blank/black | Check the path in the CSV is correct and the file exists |
| Video path warning in console | The path is returned as a string even if missing — check spelling |
| Row not advancing | Ensure the seed is set to **increment**, not fixed or random |
| `info` shows empty paths | Make sure the relevant columns exist in your CSV header row |
| no outputs being made after first run | Make sure you have set the `seed` back to 1 to start over |
| Second runs are slow | You may need to offload models between batch runs to clear the memory. Either start then stop a different model workflow quickly to force models out of memory, or restart comfyUI between batch runs |

---

## Credits

This work was based on and inspired by https://github.com/TharindaMarasingha/ComfyUI-CSV-to-Prompt

## 📄 License

MIT — free to use, modify, and share.
