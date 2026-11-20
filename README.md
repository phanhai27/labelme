<h1 align="center">
  <img src="labelme/icons/icon-256.png" width="180" height="180"><br/>Labelme — Medical DICOM & AI Edition
</h1>

<h4 align="center">
  Medical DICOM (<code>.dcm</code>) & AI-Assisted 2D Image Annotation with Python (3D Slicer Ergonomics + SAM).
</h4>

<div align="center">
  <a href="https://github.com/phanhai27/labelme/actions"><img src="https://github.com/phanhai27/labelme/actions/workflows/test.yml/badge.svg?branch=main&event=push"></a>
  <a href="https://github.com/phanhai27/labelme/releases"><img src="https://img.shields.io/github/v/release/phanhai27/labelme?include_prereleases&label=release"></a>
  <a href="https://github.com/phanhai27/labelme/blob/main/LICENSE"><img src="https://img.shields.io/github/license/phanhai27/labelme.svg"></a>
</div>

<div align="center">
  <a href="#medical--clinical-highlights"><b>Medical Highlights</b></a>
  | <a href="#installation"><b>Installation</b></a>
  | <a href="#clinical-workflows--shortcuts"><b>Clinical Workflows & Shortcuts</b></a>
  | <a href="#medical-terminology-navigator-3d-slicer-style"><b>Terminology Navigator</b></a>
  | <a href="#dicom-json-schema--pii-safety"><b>DICOM JSON Schema</b></a>
</div>

<br/>

## Overview

**Labelme (Medical DICOM & AI Edition)** is a specialized medical imaging and clinical annotation platform built on top of [Labelme](https://github.com/wkentaro/labelme) (Python + Qt6/PySide6).

While retaining full compatibility with standard 2D computer vision datasets (PNG, JPEG, TIFF, JPEG 2000, VOC/COCO export, and Segment Anything / SAM 3 AI-assisted segmentation), this edition is purpose-built for **radiologists, clinical annotators, and medical AI engineers** working with **DICOM (`.dcm`, `.dicom`)** modalities (CT, Chest X-Ray / CR / DX, MRI, Ultrasound).

______________________________________________________________________

## Medical & Clinical Highlights

- **Native 16-bit DICOM & Hounsfield Units (`HU`) Engine (`SimpleITK` + `pydicom`)**:
  - Directly decodes 16-bit raw DICOM pixel data with Modality LUT (`RescaleSlope` / `RescaleIntercept`) into 32-bit float Hounsfield Units (`HU`), supporting compressed transfer syntaxes (JPEG 2000, RLE, lossless JPEG) and automatic `MONOCHROME1` inversion.
  - **Live Slicer Data Probe**: Displays real-time physical pixel intensity (`HU: <val>` for CT or `Val: <val>`) next to cursor coordinates `(x, y)` in the status bar.
- **3D Slicer Window/Level (`WL/WW`) Presets & PACS Canvas Ergonomics**:
  - **Interactive Right-Click `WL/WW` Drag**: Adjust Window Center (`WL`, vertical drag) and Window Width (`WW`, horizontal drag) in real time directly on the canvas.
  - **One-Key Clinical Presets (`1`–`7` & `I`)**: Instant switching between `Auto Window (Header / P1–P99)`, `CT Brain`, `CT Lung`, `CT Soft Tissue`, `CT Liver`, `CT Bone`, `CT Stroke`, and `Invert Monochrome`.
  - **Hand Pan Tool (`H` / Hold `Space`) with 50% Edge Over-Pan**: Pan smoothly even while mid-drawing a polygon or AI segmentation without losing your active vertices, with 50% viewport over-pan to bring peripheral/subpleural lesions to the center of the screen.
- **3D Slicer-Style Medical Terminology Navigator (Full CRUD for Categories & Labels)**:
  - Organized by **Anatomical Categories (Groups)** and **Clinical Findings (Labels)** with distinct 3D Slicer / SNOMED-CT clinical RGB colors (preloaded with 21 chest radiograph/CT findings across 4 anatomical categories: *Lung parenchyma*, *Pleura*, *Hilum / Mediastinum*, and *Heart / Diaphragm / Trachea*).
  - **Full CRUD Management**: Add (`+`), Edit (pencil icon or context menu), and Delete (trash icon with confirmation) both custom **Anatomical Categories** and **Medical Labels**, automatically persisted to `~/.labelmerc`.
  - **Multilingual UI with 100% Canonical English JSON Output**: Displays category and finding names in the active UI language (e.g., Vietnamese, English, Japanese, etc., with seamless Linux `Fcitx5`/`IBus` IME input support) and context-aware short names inside a selected category, while always saving **100% Canonical English** labels (`shapes[*].label`) in `.json` files for standardized AI training.
- **Zero-Loss & PII-Free JSON Storage**:
  - Saves DICOM annotations with `imageData: null` (avoiding redundant base64 bloat and preserving original 16-bit `.dcm` fidelity) and stores only a strict **PII-free allowlist** of spatial and radiometric metadata (`uids`, `geometry`, `radiometry`, `viewState`) under `otherData["dicom"]`. Never exports `PatientName`, `PatientID`, `PatientBirthDate`, or `InstitutionName`.
- **AI-Assisted Segmentation (`SAM`, `EfficientSAM`, `SAM 3`, `YOLO-World`)**:
  - Interactive point/box-to-polygon and text-prompted lesion segmentation running on the currently windowed clinical view.

**🌏 Available in 21 languages** — English · Tiếng Việt · 日本語 · 한국어 · 简体中文 · 繁體中文 · Deutsch · Ελληνικά · Français · Español · Italiano · Português · Nederlands · Magyar · Русский · ไทย · Türkçe · Українська · Polski · Bahasa Indonesia · فارسی

______________________________________________________________________

## Installation

### Option 1: Standalone Desktop Installers (Recommended for Clinicians & Annotators)

No Python environment required. Download the pre-built standalone installer for your operating system from [**GitHub Releases**](https://github.com/phanhai27/labelme/releases):

- **Windows (64-bit):** `Labelme-Windows-Setup-x64.exe`
- **macOS (Apple Silicon M1/M2/M3/M4):** `Labelme-macOS-arm64.dmg`

### Option 2: Install from GitHub via `pip` / `uv` (For Medical AI Engineers)

Requires **Python 3.12 – 3.14** on 64-bit Linux, macOS, or Windows:

```bash
pip install git+https://github.com/phanhai27/labelme.git
```

Or run directly from a cloned repository using [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/phanhai27/labelme.git
cd labelme
uv sync
uv run labelme
```

______________________________________________________________________

## Clinical Workflows & Shortcuts

```bash
labelme                                    # Launch GUI (with startup splash screen)
labelme /path/to/ct_series/                # Open a folder of DICOM (.dcm) slices or 2D images
labelme slice_001.dcm --output labels/     # Save PII-free JSON annotations to a dedicated folder
```

### 1. Medical DICOM Window/Level (`WL/WW`) & Clinical Presets

| Action | Mouse / Shortcut | Window Center (`WL`) | Window Width (`WW`) | Clinical Use Case |
| :--- | :---: | :---: | :---: | :--- |
| **Interactive WL/WW Drag** | **`Right-Click Drag`** | Vertical drag (`-dy`) | Horizontal drag (`+dx`) | Real-time PACS/Slicer-style windowing on the Canvas (a stationary `Right-Click` still opens the Context Menu) |
| **Auto Window** | **`1`** | Header / `P1–P99` | Header / `P1–P99` | Restore DICOM header default or `[1%, 99%]` percentile window |
| **CT Brain** | **`2`** | `40` | `80` | Brain parenchyma window |
| **CT Lung** | **`3`** | `-600` | `1500` | Lung parenchyma & airways window |
| **CT Soft Tissue** | **`4`** | `40` | `400` | Mediastinum / abdominal soft tissue window |
| **CT Liver** | **`5`** | `60` | `160` | Hepatic parenchyma window |
| **CT Bone** | **`6`** | `400` | `1800` | Cortical & trabecular bone window |
| **CT Stroke** | **`7`** | `32` | `8` | High-contrast acute ischemic stroke window |
| **Invert Monochrome** | **`I`** | *(unchanged)* | *(unchanged)* | Toggle `MONOCHROME1` / `MONOCHROME2` inversion |

### 2. Focal Zoom & View Fitting

| Action | Mouse / Shortcut | Description |
| :--- | :--- | :--- |
| **Focal Zoom In / Out** | `Mouse Wheel` (or `Ctrl + Wheel`) | Zoom in/out anchored directly at the cursor position |
| **Step Zoom In / Out** | `Ctrl + +` / `Ctrl + -` | Zoom in or out around the viewport center |
| **Fit to Window** | `Ctrl + F` | Fit the entire slice/image inside the viewport |
| **Fit to Selection** | `Ctrl + Shift + F` | Zoom and center on the currently selected lesion(s) |
| **Actual Size (100%)** | `Ctrl + 0` | Reset zoom scale to 100% (1:1 image pixel) |

### 3. Pan (Hand Tool & 50% Viewport Edge Over-Pan)

| Action | Mouse / Shortcut | Description |
| :--- | :--- | :--- |
| **Spring-Loaded Hand Pan** | **Hold `Space` + `Left-Click Drag`** | Temporarily pan the canvas in any mode (including mid-polygon or mid-AI segmentation without losing active vertices); supports **50% viewport over-pan** to center peripheral lesions |
| **Dedicated Pan Mode** | **`H`** (or **Pan** Hand button on Toolbar) | Switch to Hand Pan mode (`Left-Click Drag` pans the image) |
| **Middle-Button Pan** | **`Middle-Click Drag`** | Pan the image at any zoom level |
| **Select / Edit Mode** | `Ctrl + J` | Switch back to Select / Edit Shapes mode |

### 4. Slice Navigation & Shape Drawing

| Action | Mouse / Shortcut | Description |
| :--- | :--- | :--- |
| **Scroll Previous / Next Slice** | **`Shift + Mouse Wheel`** | Rapidly scroll through Previous (`Wheel Up`) / Next (`Wheel Down`) slices in a study (locked while actively drawing) |
| **Previous / Next Slice** | **`A`** / **`D`** | Open the previous (`A`) or next (`D`) slice/image in the list |
| **Finalize / Close Shape** | **`Enter` (`Return`)** or `Double-Click` | Finalize and close the active `Polygon`, `LineStrip`, `AI-Segment`, or `AI-Find All` draft |
| **Undo Last Vertex** | `Backspace` / `Ctrl + Z` | Remove the last placed vertex while drawing |
| **Cancel Active Draft** | `Esc` | Discard the shape or AI draft currently being drawn |

______________________________________________________________________

## Medical Terminology Navigator (3D Slicer Style)

Modeled after 3D Slicer's *Terminologies* module, the right-hand **Label List** dock and **Shape Label** popup organize clinical findings into anatomical categories:

1. **Two Rapid Clinical Annotation Workflows**:
   - **Draw First -> Filter & Double-Click Label**: Draw a lesion on the canvas; in the `Shape Label` popup, filter by Anatomical Category or type any keyword/synonym (in English or your local language), then **Double-Click** the row to assign immediately.
   - **Pre-Select Label -> Draw Continuously**: Click a label in the right-hand `Label List` dock first (optionally disable *Show label popup on new shape* in Settings), then draw multiple lesions of that finding consecutively. Press `Esc` in the `Label List` dock to clear the pre-selection.
2. **Context-Aware Short Names**:
   - When filtering by a specific anatomical category (e.g., `Lung parenchyma` or `Pleura`), redundant anatomical prefixes are shortened (e.g., `Lung opacity` -> `Opacity`, `Pulmonary nodule` -> `Nodule`, `Pleural effusion` -> `Effusion`) for rapid visual scanning.
   - When viewing `All` categories or inspecting the `Shape List` / `Canvas`, full unambiguous names are displayed.
3. **Full CRUD for Custom Categories & Labels**:
   - **Manage Labels**: Click `+` next to the category dropdown to create a new medical label with a Canonical English ID, localized display name, anatomical category, and clinical RGB color. Hover any label row (or right-click) to **Edit** or **Delete** (with confirmation).
   - **Manage Anatomical Categories**: Inside the Medical Label dialog, click `+`, the Edit (pencil) button, or the Delete (trash) button next to the Category selector to create, rename/translate, or delete custom anatomical categories.

______________________________________________________________________

## DICOM JSON Schema & PII Safety

When annotating a DICOM file (`slice_001.dcm`), Labelme writes a companion `slice_001.json` with `imageData: null` and a strictly sanitized `otherData.dicom` block containing only spatial geometry, radiometry, and viewing parameters:

```json
{
  "version": "7.12.0",
  "flags": {},
  "shapes": [
    {
      "label": "Pulmonary nodule",
      "points": [[184.5, 210.0], [202.0, 228.5]],
      "group_id": null,
      "description": "",
      "shape_type": "rectangle",
      "flags": {},
      "mask": null
    }
  ],
  "imagePath": "slice_001.dcm",
  "imageData": null,
  "imageHeight": 512,
  "imageWidth": 512,
  "otherData": {
    "dicom": {
      "uids": {
        "sopInstanceUid": "1.2.840.113619.2.55.3.604688",
        "seriesInstanceUid": "1.2.840.113619.2.55.3.604687",
        "studyInstanceUid": "1.2.840.113619.2.55.3.604686",
        "frameOfReferenceUid": "1.2.840.113619.2.55.3.604685",
        "instanceNumber": 1
      },
      "geometry": {
        "pixelSpacingMm": [0.703125, 0.703125],
        "sliceThicknessMm": 1.25,
        "spacingBetweenSlicesMm": 1.25,
        "imagePositionPatient": [-180.0, -180.0, -45.5],
        "imageOrientationPatient": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
      },
      "radiometry": {
        "modality": "CT",
        "photometricInterpretation": "MONOCHROME2",
        "bitsStored": 16,
        "rescaleSlope": 1.0,
        "rescaleIntercept": -1024.0,
        "rescaleType": "HU",
        "headerWindowCenter": -600.0,
        "headerWindowWidth": 1500.0
      },
      "viewState": {
        "appliedWindowCenter": -600.0,
        "appliedWindowWidth": 1500.0,
        "appliedPresetName": "ct_lung",
        "isInverted": false
      }
    }
  }
}
```

______________________________________________________________________

## Development & Building Installers

Install [just](https://just.systems/man/en/packages.html) (1.58.0+) and [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
just setup   # Sync dependencies via uv
just lint    # Run ruff, gruff, ty, taplo, mdformat, yamlfix, and typos
just test    # Run unit and E2E test suites
```

To build standalone executables locally with PyInstaller:

```bash
uv run pyinstaller Labelme.spec --noconfirm
```

______________________________________________________________________

## License & Attribution

This software is distributed under the **[GNU General Public License v3.0 (GPL-3.0-only)](LICENSE)**.

- **Medical DICOM & AI Edition Maintainer (2026):** [phanhai27](https://github.com/phanhai27) (`phanhai27@gmail.com`) — Added 16-bit Medical DICOM (`SimpleITK` + `pydicom`) Hounsfield Unit windowing, clinical `WL/WW` presets, Slicer Data Probe, zero-loss PII-sanitized JSON annotation storage, 3D Slicer-style Medical Terminology Navigator with full Category/Label CRUD, PACS canvas ergonomics, Linux `Fcitx5`/`IBus` IME bridge, and standalone Windows/macOS installers.
- **Original Author & Upstream Project:** Kentaro Wada ([wkentaro/labelme](https://github.com/wkentaro/labelme), originally forked from [mpitid/pylabelme](https://github.com/mpitid/pylabelme)).
