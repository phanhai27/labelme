# Tài liệu Đặc tả Kiểm thử Hộp xám (`20261118_labelme_dicom_slicer.md`): Tích hợp DICOM Chuẩn 3D Slicer vào `Labelme`

______________________________________________________________________

## 1. Ngữ Cảnh & Mục Tiêu (Context & Rationale)

- **Tại sao tính năng này tồn tại?**: Phần mềm Desktop \[`labelme`\](file:///home/apollai/Documents/GitHub/medical/labelme) hiện chưa hỗ trợ định dạng ảnh Y tế DICOM (`.dcm`, `.dicom`). Bác sĩ và kỹ thuật viên chẩn đoán hình ảnh cần mở trực tiếp các lát cắt CT, MRI, X-quang kỹ thuật số (`DX`/`CR`) trong `Labelme` với chất lượng hiển thị tương đương **3D Slicer**, có khả năng điều chỉnh cửa sổ tín hiệu **Window Width / Window Level (WW/WL)** trên mảng dữ liệu 16-bit/float Hounsfield Unit (HU) gốc, xem giá trị `HU` thực tế dưới trỏ chuột (**Slicer Data Probe**), tận dụng AI SAM (`osam`) trên cửa sổ lâm sàng đã chọn, và lưu nhãn `.json` với độ chính xác y khoa tuyệt đối (**Zero-Loss Medical Fidelity**).
- **Kiến trúc cốt lõi (tham chiếu \[`plan_labelme_dicom_slicer.md`\](file:///home/apollai/.gemini/antigravity/brain/d37dd722-87f8-4374-8608-ecc2338e78c3/plan_labelme_dicom_slicer.md))**:
  - Sử dụng **`SimpleITK` + `pydicom`** trong module `labelme/_dicom.py` để giải mã pixel (tự động áp dụng Modality LUT: `RescaleSlope` & `RescaleIntercept`) và trích xuất metadata hình học 3D an toàn (lọc bỏ 100% PII).
  - Tuyệt đối không nhúng ảnh 8-bit vào `"imageData"` khi lưu `.json` của file DICOM đang tồn tại trên đĩa (`imageData: null`), luôn ưu tiên đọc lại mảng `float32` HU gốc từ file `.dcm` khi mở `.json`.
  - Lưu trữ trạng thái y khoa vào `annotation.other_data["dicom"]` và hiển thị giá trị `HU` / `Intensity` tại \[`StatusStats`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_status.py).

______________________________________________________________________

## 2. Tiền điều kiện & Dữ liệu Kiểm thử Thực tế (Preconditions & Realistic Seed Data)

1. **Môi trường thực thi**:
   - Workspace: `/home/apollai/Documents/GitHub/medical/labelme`
   - Python `>=3.12`, `PySide6>=6.8`, `SimpleITK>=2.3.0`, `pydicom>=2.4.0`, chạy kiểm thử với `QT_QPA_PLATFORM=offscreen`.
2. **Dữ liệu DICOM thực tế và giả lập chuẩn lâm sàng**:
   - Có sẵn tập file DICOM mẫu thực tế tại `/home/apollai/Documents/GitHub/medical/image-annotator/images/Patient001/instance-0001.dcm`.
   - Trong bộ test tự động (`tests/unit/test_dicom.py`), sinh thêm các file DICOM chuẩn y khoa bằng `pydicom` / `SimpleITK` trong `tmp_path` bám sát thông số lâm sàng thực tế (không dùng dữ liệu giả vô nghĩa):
     - **Mẫu CT Ngực (`chest_ct_slice.dcm`)**: `Modality = "CT"`, `Rows = 128`, `Columns = 128`, `BitsAllocated = 16`, `PixelRepresentation = 1` (signed `int16`), `RescaleSlope = 1.0`, `RescaleIntercept = -1024.0`, chứa vùng khí quản (`HU = -950`), nhu mô phổi (`HU = -600`), mô mềm trung thất (`HU = +45`), và xương đốt sống ngực (`HU = +750`), `WindowCenter = -600`, `WindowWidth = 1500`, `PhotometricInterpretation = "MONOCHROME2"`, `PixelSpacing = [0.703125, 0.703125]`, `SliceThickness = 1.25`, `ImagePositionPatient = [-180.0, -180.0, -45.5]`, `ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]`. Đi kèm các tag PII giả lập (`PatientName = "NGUYEN^VAN^AN"`, `PatientID = "BN-2026-9981"`, `PatientBirthDate = "19750412"`, `InstitutionName = "Benh Vien Cho Ray"`) để kiểm thử bộ lọc bảo mật PII.
     - **Mẫu X-quang Ngực `MONOCHROME1` (`chest_dx_mono1.dcm`)**: `Modality = "DX"`, `PhotometricInterpretation = "MONOCHROME1"`, kiểm thử đảo ngược thang xám đúng chuẩn DICOM.
     - **Mẫu X-quang Ngực `MONOCHROME2` (`chest_dx_mono2.dcm`)**: `Modality = "DX"`, `PhotometricInterpretation = "MONOCHROME2"`, đảm bảo **không bị đảo ngược sai** thành âm bản.

______________________________________________________________________

## 3. Hợp đồng Định danh Kỹ thuật & Hooks (`Test Hooks & Contracts`)

### 3.1. Module `labelme/_dicom.py` (Engine & Metadata Contract)

- **Hàm nhận diện**: `is_dicom_file(*, filename: str | Path) -> bool` — trả về `True` cho đuôi `.dcm`, `.dicom` (không phân biệt hoa thường).
- **Cấu trúc dữ liệu phiên DICOM (`DicomSessionData` / `DicomMetadata`)**:
  - `hu_array: NDArray[np.float32]` (mảng 2D `(H, W)` chứa giá trị vật lý sau khi áp dụng `RescaleSlope` & `RescaleIntercept`).
  - `rgb_array: NDArray[np.uint8]` (nếu `PhotometricInterpretation == "RGB"` hoặc ảnh màu siêu âm).
  - `modality: str | None`
  - `photometric_interpretation: str`
  - `window_center: float`
  - `window_width: float`
  - `is_inverted: bool`
  - `preset_name: str`
  - `metadata_dict: dict[str, Any]` (cấu trúc chuẩn để ghi vào `other_data["dicom"]`).
- **Hàm áp dụng cửa sổ tín hiệu**:
  - `apply_dicom_window(*, hu_array: NDArray[np.float32], window_center: float, window_width: float, invert: bool = False) -> NDArray[np.uint8]`
- **Danh sách Clinical Presets (`DICOM_WINDOW_PRESETS`)**:
  - `"auto"`: lấy theo tag DICOM hoặc phân vị `1st–99th percentile`.
  - `"ct_brain"`: `(40.0, 80.0)`
  - `"ct_lung"`: `(-600.0, 1500.0)`
  - `"ct_soft_tissue"`: `(40.0, 400.0)`
  - `"ct_liver"`: `(60.0, 160.0)`
  - `"ct_bone"`: `(400.0, 1800.0)`
  - `"ct_stroke"`: `(32.0, 8.0)`

### 3.2. Hợp đồng Cấu trúc JSON `other_data["dicom"]` trong File Nhãn `.json`

Khi lưu file `.json` cho ảnh DICOM, payload JSON bắt buộc tuân thủ:

- Trường gốc `"imageData"`: `null` (khi `with_image_data` tắt hoặc đối với file `.dcm` tồn tại trên đĩa nhằm bảo toàn đọc trực tiếp từ `.dcm`).
- Trường gốc `"dicom"` (nằm trong `annotation.other_data["dicom"]`):
  - `"uids"`: `{"sopInstanceUid": str | None, "seriesInstanceUid": str | None, "studyInstanceUid": str | None, "frameOfReferenceUid": str | None, "instanceNumber": int | None}`
  - `"geometry"`: `{"pixelSpacingMm": [float, float] | None, "sliceThicknessMm": float | None, "spacingBetweenSlicesMm": float | None, "imagePositionPatient": [float, float, float] | None, "imageOrientationPatient": [float, float, float, float, float, float] | None}`
  - `"radiometry"`: `{"modality": str | None, "photometricInterpretation": str | None, "bitsStored": int | None, "rescaleSlope": float, "rescaleIntercept": float, "rescaleType": str | None, "headerWindowCenter": float | None, "headerWindowWidth": float | None}`
  - `"viewState"`: `{"appliedWindowCenter": float, "appliedWindowWidth": float, "appliedPresetName": str, "isInverted": bool}`
- **Chốt chặn Bảo mật PII**: Tuyệt đối không tồn tại bất kỳ chuỗi nào thuộc `PatientName`, `PatientID`, `PatientBirthDate`, `InstitutionName` trong toàn bộ nội dung file `.json` xuất ra.

### 3.3. Hợp đồng Giao diện PySide6 (`Widgets & Status Bar Hooks`)

- **\[`StatusStats`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_status.py)**:
  - Phương thức `set_position(*, x: float, y: float, intensity_text: str | None = None) -> None`.
  - Khi mở ảnh thường: hiển thị `x  120   y   85`.
  - Khi mở ảnh DICOM: hiển thị `x  120   y   85   HU: -600` (nếu `Modality == "CT"` hoặc `rescaleType == "HU"`) hoặc `x  120   y   85   Val: 1024` (với các modality khác).
- **\[`BrightnessContrastDialog`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_brightness_contrast_dialog.py)**:
  - Hỗ trợ truyền dữ liệu DICOM 16-bit/float (`hu_array: NDArray[np.float32] | None = None`, `window_center: float | None = None`, `window_width: float | None = None`, `invert: bool = False`, `preset_name: str = "auto"`).
  - Các điều khiển (Widgets) truy xuất được trong `pytest-qt`:
    - `combo_preset: QtWidgets.QComboBox` (chỉ hiển thị khi ở chế độ DICOM)
    - `spin_window_center: QtWidgets.QDoubleSpinBox` / `slider_window_center: QtWidgets.QSlider`
    - `spin_window_width: QtWidgets.QDoubleSpinBox` / `slider_window_width: QtWidgets.QSlider`
    - `check_invert: QtWidgets.QCheckBox`

______________________________________________________________________

## 4. Kịch bản Kiểm thử Hộp xám Chi tiết (`Grey-box Test Scenarios`)

### `TC-DCM-01`: Nhận diện đuôi file `.dcm` / `.dicom` và Quét thư mục

- **Luồng thực thi**: Gọi \[`_list_supported_image_extensions()`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_app.py#L5040-L5047) và \[`_scan_image_files(root_dir=...)`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_app.py#L5059-L5086) trên thư mục chứa cả `.dcm`, `.dicom`, `.png`, `.json`.
- **Xác minh Hộp xám**: Danh sách trả về có mặt đầy đủ `.dcm` và `.dicom` được sắp xếp tự nhiên (`natsort`), bỏ qua file `.json`.

### `TC-DCM-02`: Chuẩn hóa Modality LUT (Hounsfield Unit) bằng `SimpleITK` + `pydicom`

- **Luồng thực thi**: Đọc file `chest_ct_slice.dcm` có `RescaleSlope = 1.0`, `RescaleIntercept = -1024.0`, với pixel lưu trữ thô bằng `424` (tương ứng nhu mô phổi `-600 HU`) và `1774` (tương ứng xương `+750 HU`).
- **Xác minh Hộp xám**: Mảng `hu_array` trong phiên DICOM có giá trị chính xác `-600.0` và `+750.0` (`dtype == np.float32`). Khi áp cửa sổ Phổi (`WL = -600, WW = 1500`), điểm `-600 HU` ánh xạ ra đúng mức xám giữa `127/128` (`uint8`), trong khi điểm xương `+750 HU` vượt ngưỡng trên (`+150 HU`) ánh xạ ra `255` (trắng).

### `TC-DCM-03`: Quy tắc Đảo màu chuẩn Y khoa (`MONOCHROME1` vs `MONOCHROME2`)

- **Luồng thực thi**: Giải mã 2 file X-quang `Modality = "DX"` có cùng mảng pixel nhưng khác `PhotometricInterpretation` (`MONOCHROME1` so với `MONOCHROME2`).
- **Xác minh Hộp xám**:
  - File `MONOCHROME2` giữ nguyên chiều sáng tối (`0` là đen, giá trị cao là trắng), **không bị đảo ngược sai** như lỗi cũ của `image-annotator`.
  - File `MONOCHROME1` tự động được đảo ngược (`0` thành `255`, giá trị cao thành `0`).

### `TC-DCM-04`: Chốt chặn Bảo mật Lọc PII Bệnh nhân (Strict Allowlist)

- **Luồng thực thi**: Mở `chest_ct_slice.dcm` trong `MainWindow` (qua `qtbot`), tạo một nhãn đa giác (`polygon`), lưu ra file `chest_ct_slice.json`.
- **Xác minh Hộp xám**:
  - Đọc nội dung văn bản thô của `chest_ct_slice.json`: tuyệt đối không chứa `"NGUYEN"`, `"BN-2026-9981"`, `"19750412"`, `"Cho Ray"`, `"PatientName"`, `"PatientID"`.
  - Khối `data["dicom"]["geometry"]` chứa chính xác `pixelSpacingMm == [0.703125, 0.703125]`, `sliceThicknessMm == 1.25`, `imagePositionPatient == [-180.0, -180.0, -45.5]`, `imageOrientationPatient == [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]`.

### `TC-DCM-05`: Tương tác Cửa sổ WW/WL & Clinical Presets không làm mất dải động 16-bit

- **Luồng thực thi**: Mở `chest_ct_slice.dcm` trên `MainWindow`. Mở hộp thoại WW/WL (`BrightnessContrastDialog`), chuyển `combo_preset` sang `"ct_bone"` (`WL = 400, WW = 1800`), sau đó chuyển tiếp sang `"ct_lung"` (`WL = -600, WW = 1500`) và bật/tắt `check_invert`.
- **Xác minh Hộp xám**:
  - Ở chế độ `"ct_bone"`, vùng khí và nhu mô phổi (`-600 HU`) bị cắt về `0` (đen), trong khi vùng xương (`+750 HU`) hiển thị chi tiết rõ nét (không bị bão hòa `255`).
  - Khi chuyển ngược về `"ct_lung"`, vùng nhu mô phổi (`-600 HU`) khôi phục lại đúng mức xám `127/128` từ mảng `hu_array` gốc mà không bị mất mát dữ liệu do lần cắt trước đó.
  - Khóa `Canvas.pixmap.cacheKey()` thay đổi sau mỗi lần đổi cửa sổ để kích hoạt làm mới cho AI SAM (`osam`).

### `TC-DCM-06`: Khôi phục Trạng thái WW/WL và Đọc Trực tiếp từ `.dcm` Gốc ("Zero-Loss")

- **Luồng thực thi**: Chỉnh cửa sổ của `chest_ct_slice.dcm` sang `WL = 40, WW = 400` (*CT Soft Tissue*), lưu file `.json`. Đóng file và mở lại file `.json` vừa lưu.
- **Xác minh Hộp xám**:
  - Trong file `.json`, `"imageData"` là `null`.
  - Khi mở lại `.json`, `MainWindow` đọc lại mảng `hu_array` 16-bit/float từ `chest_ct_slice.dcm` và tự động khôi phục đúng cửa sổ `WL = 40.0, WW = 400.0` từ `other_data["dicom"]["viewState"]`.

### `TC-DCM-07`: Slicer Data Probe trên Thanh trạng thái (`StatusStats`)

- **Luồng thực thi**: Mở `chest_ct_slice.dcm` trên `MainWindow`, mô phỏng di chuyển chuột tới tọa độ pixel `(x=64, y=64)` nơi có giá trị `-600 HU`.
- **Xác minh Hộp xám**: Nhãn văn bản của `MainWindow._status_bar.stats.text()` hiển thị tọa độ kèm chuỗi `HU: -600`. Khi mở tiếp một ảnh `.jpg` thông thường, nhãn `StatusStats` tự động trở về định dạng `x ... y ...` không còn hậu tố `HU:`.

### `TC-DCM-08`: Kiểm tra Giới hạn Bộ nhớ Giải mã (`_check_decodable`) với DICOM Khổng lồ

- **Luồng thực thi**: Hạ giới hạn bộ nhớ giải mã xuống `1 MB` qua fixture `set_allocation_limit(1)` và gọi `read_image_file` trên một file DICOM `1024x1024` (cần 4 MB bộ nhớ Qt).
- **Xác minh Hộp xám**: Hệ thống ném đúng ngoại lệ \[`ImageDecodeLimitError`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_label_file.py#L281-L298) ngay từ bước đọc header trước khi nạp mảng pixel.

### `TC-DCM-09`: Xử lý File DICOM Thực tế trong Workspace (`Patient001`)

- **Luồng thực thi**: Mở trực tiếp file `/home/apollai/Documents/GitHub/medical/image-annotator/images/Patient001/instance-0001.dcm` bằng `read_image_file` và `MainWindow`.
- **Xác minh Hộp xám**: Ảnh được giải mã thành công sang `QImage` hợp lệ (`not image.isNull()`), trích xuất đúng kích thước và hiển thị lên `Canvas` không phát sinh cảnh báo hay ngoại lệ.

### `TC-DCM-10`: Giữ Cửa sổ WW/WL Xuyên Chuỗi Lát cắt (`Keep Previous Window/Level`)

- **Luồng thực thi**: Mở thư mục chứa 2 lát cắt DICOM liên tiếp (`slice_01.dcm`, `slice_02.dcm`), bật hành động `toggle_keep_prev_brightness_contrast`, chỉnh `slice_01.dcm` sang cửa sổ *CT Bone* (`WL = 400, WW = 1800`), rồi bấm chuyển sang `slice_02.dcm`.
- **Xác minh Hộp xám**: Lát cắt `slice_02.dcm` tự động được áp cửa sổ `WL = 400, WW = 1800` ngay khi vừa tải lên.

______________________________________________________________________

## 5. Chốt chặn Nghiệm thu Kỹ thuật (Definition of Done / Verification Gate)

Subagent thực thi chỉ được phép báo cáo hoàn thành khi chạy vượt qua 100% các lệnh kiểm tra sau trong `/home/apollai/Documents/GitHub/medical/labelme`:

1. **Unit & GUI Tests**: Chạy `pytest tests/unit/test_dicom.py` và các bài test liên quan (`test_label_file`, `test_app`, `test_brightness_contrast`) đạt **100% PASS**.
2. **Code Style & Linter**: Chạy `ruff check` và `gruff` (tuân thủ nghiêm ngặt quy tắc `keyword-only arguments (*, ...)` và `force-single-line` imports của dự án `labelme`) đạt **0 lỗi**.
3. **Type Check**: Chạy `ty check` (hoặc trình kiểm tra kiểu của repo) đạt **0 lỗi**.
