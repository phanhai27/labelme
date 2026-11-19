<h1 align="center">
  <img src="labelme/icons/icon-256.png" width="200" height="200"><br/>labelme
</h1>

<h4 align="center">
  Image annotation with Python.
</h4>

<div align="center">
  <a href="https://pypi.python.org/pypi/labelme"><img src="https://img.shields.io/pypi/v/labelme.svg"></a>
  <!-- <a href="https://pypi.org/project/labelme"><img src="https://img.shields.io/pypi/pyversions/labelme.svg"></a> -->
  <a href="https://github.com/wkentaro/labelme/actions"><img src="https://github.com/wkentaro/labelme/actions/workflows/test.yml/badge.svg?branch=main&event=push"></a>
  <a href="https://discord.com/invite/uAjxGcJm83"><img src="https://dcbadge.limes.pink/api/server/uAjxGcJm83?style=flat"></a>
</div>

<div align="center">
  <a href="#installation"><b>Installation</b></a>
  | <a href="#usage"><b>Usage</b></a>
  | <a href="#examples"><b>Examples</b></a>
  <!-- | <a href="https://github.com/wkentaro/labelme/discussions"><b>Community</b></a> -->
  <!-- | <a href="https://www.youtube.com/playlist?list=PLI6LvFw0iflh3o33YYnVIfOpaO0hc5Dzw"><b>Youtube FAQ</b></a> -->
</div>

<br/>

<div align="center">
  <img src="examples/instance_segmentation/.readme/annotation.jpg" width="70%">
</div>

## Description

Labelme is a graphical image annotation tool inspired by http://labelme.csail.mit.edu.
It is written in Python and uses Qt for its graphical interface.
This fork extends the original tool with medical imaging support (including DICOM).

<img src="examples/instance_segmentation/data_dataset_voc/JPEGImages/2011_000006.jpg" width="19%" /> <img src="examples/instance_segmentation/data_dataset_voc/SegmentationClass/2011_000006.png" width="19%" /> <img src="examples/instance_segmentation/data_dataset_voc/SegmentationClassVisualization/2011_000006.jpg" width="19%" /> <img src="examples/instance_segmentation/data_dataset_voc/SegmentationObject/2011_000006.png" width="19%" /> <img src="examples/instance_segmentation/data_dataset_voc/SegmentationObjectVisualization/2011_000006.jpg" width="19%" />\
<i>VOC dataset example of instance segmentation.</i>

<img src="examples/semantic_segmentation/.readme/annotation.jpg" width="30%" /> <img src="examples/bbox_detection/.readme/annotation.jpg" width="30%" /> <img src="examples/classification/.readme/annotation_cat.jpg" width="35%" />\
<i>Other examples (semantic segmentation, bbox detection, and classification).</i>

<img src="https://user-images.githubusercontent.com/4310419/47907116-85667800-de82-11e8-83d0-b9f4eb33268f.gif" width="30%" /> <img src="https://user-images.githubusercontent.com/4310419/47922172-57972880-deae-11e8-84f8-e4324a7c856a.gif" width="30%" /> <img src="https://user-images.githubusercontent.com/14256482/46932075-92145f00-d080-11e8-8d09-2162070ae57c.png" width="32%" />\
<i>Various primitives (polygon, rectangle, circle, line, and point).</i>

<img src="https://github.com/user-attachments/assets/53bf09db-b097-48b7-9f32-ab490da5ac53" width="32%" />
<p><i>Multi-language support (English, 中文, 日本語, 한국어, Deutsch, Français, and more).</i></p>

## Features

- [x] Image annotation for polygon, rectangle, circle, line and point ([tutorial](examples/tutorial))
- [x] Image flag annotation for classification and cleaning ([#166](https://github.com/wkentaro/labelme/pull/166))
- [x] Video annotation ([video annotation](examples/video_annotation))
- [x] GUI customization (predefined labels / flags, auto-saving, label validation, etc) ([#144](https://github.com/wkentaro/labelme/pull/144))
- [x] Exporting VOC-format dataset for [semantic segmentation](examples/semantic_segmentation), [instance segmentation](examples/instance_segmentation)
- [x] Exporting COCO-format dataset for [instance segmentation](examples/instance_segmentation)
- [x] AI-assisted point-to-polygon/mask annotation by SAM, EfficientSAM models
- [x] AI text-to-annotation by YOLO-world, SAM3 models
- [x] Medical DICOM (`.dcm`, `.dicom`) 16-bit Hounsfield Unit support (`SimpleITK` + `pydicom`), clinical Window/Level (`WL/WW`) presets, Slicer Data Probe (`HU` readout under cursor), and zero-loss JSON annotation storage (`imageData: null`)
- [x] 3D Slicer-style Medical Terminology Navigator with 21 predefined clinical labels across 4 anatomical categories, locale-aware bilingual UI display (`en_US` / `vi_VN`), context-aware short names within categories, smart keyword/alias search, custom label form dialog (`+`), and 100% canonical English JSON output

**🌏 Available in 21 languages** - English · 日本語 · 한국어 · 简体中文 · 繁體中文 · Deutsch · Ελληνικά · Français · Español · Italiano · Português · Nederlands · Magyar · Русский · ไทย · Tiếng Việt · Türkçe · Українська · Polski · Bahasa Indonesia · فارسی (`LANG=ja_JP.UTF-8 labelme`)

## Installation

There are 3 options to install labelme:

### Option 1: Using pip

For more detail, check ["Install Labelme using Terminal"](https://www.labelme.io/docs/install-labelme-terminal)

```bash
pip install labelme

# To install the latest version from GitHub:
# pip install git+https://github.com/wkentaro/labelme.git
```

### Option 2: Using standalone executable (Easiest)

If you're willing to invest in the convenience of simple installation without any dependencies (Python, Qt),
you can download the standalone executable from ["Install Labelme as App"](https://www.labelme.io/docs/install-labelme-app).

It's a one-time payment for lifetime access, and it helps us to maintain this project.

### Option 3: Linux distribution packages

On some Linux distributions, labelme is also packaged in the system's native repository and can be installed with the distribution's standard package tooling. The badge below tracks which distributions currently ship labelme and which version each one provides:

[![Packaging status](https://repology.org/badge/vertical-allrepos/labelme.svg)](https://repology.org/project/labelme/versions)

### Supported Python and platforms

| | Supported (v7.x) | Maintenance (v6.3.x) |
| ------ | ------------------------------ | -------------------- |
| Python | 3.12 - 3.14 | 3.10 - 3.11 |
| Qt | Qt6 (PySide6) | Qt5 |
| OS | 64-bit macOS / Windows / Linux | older OSes |

labelme follows [SPEC 0](https://scientific-python.org/specs/spec-0000/) (the successor to [NEP 29](https://numpy.org/neps/nep-0029-deprecation_policy.html)) for dropping Python versions, in step with its core scientific dependencies (numpy, scipy, scikit-image). v6.3.x is the maintenance line for Qt5 and Python 3.10 / 3.11 stragglers.

v6.3.x receives critical fixes only, on a best-effort basis with no release cadence or SLA. "Critical" is limited to:

- security vulnerabilities,
- data-loss or annotation-corruption bugs,
- install or launch breakage caused by upstream dependency drift.

Feature backports and non-critical bugs are out of scope; all new development happens on v7.x.

### Upgrading from v6.x to v7

v7.0.0 raises the platform floor:

- **Qt binding:** the GUI moved from PyQt5 (Qt5) to PySide6 (Qt6). `pip install labelme` now pulls PySide6 instead of PyQt5.
- **Python:** the minimum is now Python 3.12 (3.10 and 3.11 are dropped).
- **OS:** Qt6 requires a 64-bit macOS, Windows, or Linux; older OSes that only Qt5 supported are no longer covered.
- **No public Python API:** labelme is an application, not a library, and exposes no stable Python API. Its internal modules were privatized in v7 (renamed to underscore-prefixed names), so `import labelme.app`, `labelme.utils`, `labelme.widgets`, and similar imports no longer work. If you previously imported labelme internals, pin `labelme<7` and vendor the code you need; see [`examples/utils.py`](examples/utils.py) for copy-and-adapt reference code that reads the JSON annotation format without depending on labelme.

If you need to stay on PyQt5/Qt5, Python 3.10 or 3.11, or an older OS, pin to the v6.3.x maintenance line:

```bash
pip install 'labelme<7'
```

All previous releases remain installable from [PyPI](https://pypi.org/project/labelme/#history), so existing pins keep working.

v7.0.0 also changes config parsing:

- **Config booleans:** `~/.labelmerc` is now parsed with ruamel.yaml (YAML 1.2), so the boolean spellings `yes`/`no`/`on`/`off` (in any capitalization) are read as strings rather than booleans. If you set any boolean option this way, switch it to `true`/`false`.

### Public interface

labelme is an application. The interfaces you can build on and that we keep stable are:

- the **command-line interface** (`labelme ...`),
- the **on-disk JSON annotation format**, and
- the **`~/.labelmerc` config format**.

Everything else, including the Python import surface, is internal and may change or be renamed without notice. To consume annotations from your own code, read the JSON format directly (see [`examples/utils.py`](examples/utils.py)).

## Usage

Run `labelme --help` for detail.\
The annotations are saved as a [JSON](http://www.json.org/) file.

JPEG 2000 images (`.jp2`, `.jpx`, `.j2k`, `.j2c`) can be opened, scanned from a
folder, or dragged into the window when Pillow has OpenJPEG support. They are
decoded to PNG in memory for Qt, preserving pixel values and transparency;
the source image is unchanged.

Medical DICOM images (`.dcm`, `.dicom`) are decoded directly from 16-bit raw pixel data with Modality LUT (`RescaleSlope` / `RescaleIntercept`) into 32-bit float Hounsfield Units (`HU`) via `SimpleITK` and `pydicom`. Annotations are saved with `imageData: null`, strictly sanitized PII-free 3D spatial geometry (`pixelSpacingMm`, `sliceThicknessMm`, `imagePositionPatient`, `imageOrientationPatient`), and the active `viewState` (`appliedWindowCenter`, `appliedWindowWidth`, `appliedPresetName`, `isInverted`).

```bash
labelme  # just open gui

# tutorial (single image example)
cd examples/tutorial
labelme apc2016_obj3.jpg  # specify image file
labelme apc2016_obj3.jpg --output annotations/  # read and save annotation files in an annotation folder
labelme apc2016_obj3.jpg --with-image-data  # include image data in JSON file
labelme apc2016_obj3.jpg \
  --labels highland_6539_self_stick_notes,mead_index_cards,kong_air_dog_squeakair_tennis_ball  # specify label list

# semantic segmentation example
cd examples/semantic_segmentation
labelme data_annotated/  # Open a folder to annotate all images in it
labelme data_annotated/ --labels labels.txt  # specify label list with a file
```

### Mouse & Keyboard Shortcuts (Canvas Navigation, Drawing & Medical DICOM)

#### 1. Focal Zoom & View Fitting

| Action | Mouse / Shortcut | Description |
| :--- | :--- | :--- |
| **Focal Zoom In / Out** | `Mouse Wheel` (or `Ctrl + Wheel`) | Zoom in/out directly anchored at the cursor position |
| **Step Zoom In / Out** | `Ctrl + +` / `Ctrl + -` | Zoom in or out around the viewport center |
| **Fit to Window** | `Ctrl + F` | Fit the entire image inside the viewport |
| **Fit to Selection** | `Ctrl + Shift + F` | Zoom and center on the currently selected shapes |
| **Actual Size (100%)** | `Ctrl + 0` | Reset zoom scale to 100% |

#### 2. Pan (Hand Tool & 50% Viewport Edge Over-pan)

| Action | Mouse / Shortcut | Description |
| :--- | :--- | :--- |
| **Spring-loaded Hand Pan** | **Hold `Space` + `Left-Click Drag`** | Temporarily pan the canvas in any mode (including while mid-drawing a `Polygon` or `AI-Segment` without closing or losing the active draft); supports **50% viewport over-pan** to center peripheral/edge lesions |
| **Pan Tool Mode** | **`H`** (or **Pan** button on Left Toolbar) | Switch to dedicated Hand Pan mode (`Left-Click Drag` pans the image) |
| **Middle-Button Pan** | **`Middle-Click Drag`** | Pan the image at any zoom level |
| **Select / Edit Mode** | `Ctrl + J` | Switch back to Select / Edit Shapes mode |

#### 3. Drawing & Finalizing Annotations

| Action | Mouse / Shortcut | Description |
| :--- | :--- | :--- |
| **Finalize / Close Shape** | **`Enter` (`Return`)** or `Double-Click` | Finalize and close the active `Polygon`, `LineStrip`, `AI-Segment`, or `AI-Find All` draft |
| **Undo Last Point** | `Backspace` / `Ctrl + Z` | Remove the last placed vertex while drawing |
| **Cancel Active Draft** | `Esc` | Discard the shape or AI draft currently being drawn |

#### 4. Image / Slice Navigation

| Action | Mouse / Shortcut | Description |
| :--- | :--- | :--- |
| **Scroll Previous / Next Slice** | **`Shift + Mouse Wheel`** | Rapidly scroll through Previous (`Wheel Up`) / Next (`Wheel Down`) slices or images in the folder (automatically locked while actively drawing a shape) |
| **Previous / Next Image** | **`A`** / **`D`** | Open the previous (`A`) or next (`D`) image/slice in the list |
| **Scrollbar Scroll** | `Alt + Mouse Wheel` | Traditional vertical/horizontal scrollbar scrolling |

#### 5. Medical DICOM Window/Level (`WL/WW`) & Clinical Presets

| Action | Mouse / Shortcut | Window Center (`WL`) | Window Width (`WW`) | Description |
| :--- | :---: | :---: | :---: | :--- |
| **Interactive WL/WW Drag** | **`Right-Click Drag`** | Vertical drag (`-dy`) | Horizontal drag (`+dx`) | Real-time PACS/Slicer-style windowing directly on the Canvas (a stationary `Right-Click` still opens the Context Menu) |
| **Auto Window** | **`1`** | Header / `P1–P99` | Header / `P1–P99` | Restore default DICOM header or percentile `[1%, 99%]` window |
| **CT Brain** | **`2`** | `40` | `80` | Brain parenchyma window |
| **CT Lung** | **`3`** | `-600` | `1500` | Lung parenchyma window |
| **CT Soft Tissue** | **`4`** | `40` | `400` | Mediastinum / soft tissue window |
| **CT Liver** | **`5`** | `60` | `160` | Hepatic parenchyma window |
| **CT Bone** | **`6`** | `400` | `1800` | Cortical / trabecular bone window |
| **CT Stroke** | **`7`** | `32` | `8` | High-contrast acute ischemic stroke window |
| **Invert Monochrome** | **`I`** | *(unchanged)* | *(unchanged)* | Toggle monochrome inversion (`MONOCHROME1` / `MONOCHROME2`) |

#### 6. Medical Terminology Navigator & Anatomical Category Filtering (3D Slicer Style)

Labelme includes a built-in **Medical Terminology Navigator** modeled after 3D Slicer's *Terminologies* module, preloaded with **21 clinical findings** organized into **4 anatomical categories** (`Lung parenchyma`, `Pleura`, `Hilum / Mediastinum`, and `Heart / Diaphragm / Trachea`) with distinct clinical RGB colors:

- **Locale-Aware UI Display (`en_US` / `vi_VN`)**: Automatically displays Vietnamese medical terms when the UI language is set to Vietnamese (`File -> Settings -> Language -> Tiếng Việt`) and English terms when set to English.
- **Context-Aware Short Names**: When filtering by a specific anatomical category (e.g., `Lung parenchyma` or `Pleura`), redundant anatomical prefixes are shortened (`Lung opacity` -> `Opacity` / `Đám mờ phổi` -> `Đám mờ`; `Pleural effusion` -> `Effusion` / `Tràn dịch màng phổi` -> `Tràn dịch`) for rapid scanning. When viewing `All` categories or inspecting the `Shape List` / `Canvas`, full unambiguous names are shown.
- **100% Canonical English JSON Output**: Regardless of the active UI language or whether a short category name was clicked, all annotations written to `.json` files (`shapes[*].label`) are stored in **100% Canonical English** (e.g., `"Lung opacity"`, `"Pulmonary nodule"`, `"Pleural calcification"`) for downstream AI training.
- **Two Rapid Clinical Annotation Workflows**:
  1. **Draw First -> Double-Click Label**: Draw a lesion on the canvas; in the `Shape Label` popup, filter by Anatomical Category or type any keyword/synonym (English, Vietnamese, or unaccented text such as `"opacity"`, `"collapse"`, `"deviation"`, `"đông đặc"`, `"dong dac"`), then **Double-Click** the row to assign immediately.
  2. **Pre-Select Label -> Draw Continuously**: Click a label in the right-hand `Label List` dock first (optionally disable *Show label popup on new shape* in Settings), then draw multiple lesions of that finding consecutively. Press `Esc` in the `Label List` dock to clear the pre-selection.
- **Add Custom Medical Labels (`+`)**: Click the `+` button next to the category dropdown in the `Label List` dock or `Shape Label` popup to add new clinical findings or custom anatomical categories via a validated Form UI (enforcing a non-empty ASCII Canonical English ID for AI JSON export) and persist them automatically to `~/.labelmerc`.

### Command Line Arguments

Run `labelme --help` for the full list.

### FAQ

- **How to convert JSON file to numpy array?** See [examples/tutorial](examples/tutorial#convert-to-dataset).
- **How to load label PNG file?** See [examples/tutorial](examples/tutorial#how-to-load-label-png-file).
- **How to get annotations for semantic segmentation?** See [examples/semantic_segmentation](examples/semantic_segmentation).
- **How to get annotations for instance segmentation?** See [examples/instance_segmentation](examples/instance_segmentation).

## Examples

- [Image Classification](examples/classification)
- [Bounding Box Detection](examples/bbox_detection)
- [Semantic Segmentation](examples/semantic_segmentation)
- [Instance Segmentation](examples/instance_segmentation)
- [Video Annotation](examples/video_annotation)

## How to build standalone executable

```bash
LABELME_PATH=./labelme
OSAM_PATH=$(python -c 'import os, osam; print(os.path.dirname(osam.__file__))')
pyinstaller labelme/labelme/__main__.py \
  --name=Labelme \
  --windowed \
  --noconfirm \
  --specpath=build \
  --add-data=$(OSAM_PATH)/_models/yoloworld/clip/bpe_simple_vocab_16e6.txt.gz:osam/_models/yoloworld/clip \
  --add-data=$(LABELME_PATH)/_config/default_config.yaml:labelme/_config \
  --add-data=$(LABELME_PATH)/icons/*:labelme/icons \
  --add-data=$(LABELME_PATH)/translate/*:translate \
  --icon=$(LABELME_PATH)/icons/icon-256.png \
  --onedir
```

## Development

Install [just](https://just.systems/man/en/packages.html) 1.58.0 or newer and
[uv](https://docs.astral.sh/uv/getting-started/installation/). Recipes use Bash;
on Windows, install Git for Windows and make its Bash available on `PATH`.

Run `just` to list commands and their arguments. Common commands are
`just setup`, `just lint`, and `just test`.

## Acknowledgement

This repo is a fork of [wkentaro/labelme](https://github.com/wkentaro/labelme) (originally forked from [mpitid/pylabelme](https://github.com/mpitid/pylabelme)).
