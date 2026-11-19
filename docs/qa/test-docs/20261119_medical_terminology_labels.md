# Đặc Tả Kiểm Thử Hộp Xám (QA Test Docs / ATDD Contract): Bộ Từ Vựng Y Khoa & Chọn Nhãn Kiểu 3D Slicer

- **Mã tài liệu:** `20261119_medical_terminology_labels.md`
- **Ngày lập:** `2026-11-19`
- **Phạm vi kiểm thử:** Desktop Application (`PySide6` / `pytest-qt` Unit & E2E Tests)

______________________________________________________________________

## 1. Ngữ Cảnh & Mục Tiêu (Context & Rationale)

- **Tại sao tính năng này tồn tại?**
  - Bác sĩ chẩn đoán hình ảnh khi đọc phim X-quang / DICOM trên Labelme cần chọn nhanh vùng bệnh lý từ danh sách chuẩn (như module **Terminologies** của **3D Slicer**) thay vì gõ tay từng nhãn.
  - Bác sĩ dùng giao diện Tiếng Việt muốn nhìn thấy tên bệnh bằng Tiếng Việt (hoặc Tiếng Anh nếu dùng giao diện Tiếng Anh), và khi lọc vào 1 nhóm giải phẫu cụ thể (*Nhu mô phổi*, *Màng phổi*...) thì tên nhãn phải được rút gọn phần tiền tố lặp lại (VD: `Lung opacity` $\\rightarrow$ `Opacity`, `Đám mờ phổi` $\\rightarrow$ `Đám mờ`).
  - Trong khi đó, file `.json` lưu xuống đĩa cứng để huấn luyện AI bắt buộc phải lưu **100% mã chuẩn Tiếng Anh đầy đủ** (`"Lung opacity"`, `"Pulmonary nodule"`...).
  - Bác sĩ có thể chuyển đổi Bộ nhãn (Preset) hoặc tự bổ sung nhãn mới thông qua **Form UI có kiểm soát** (không nạp từ file ngoài để tránh lỗi định dạng).

______________________________________________________________________

## 2. Tiền Điều Kiện (Preconditions)

1. **Môi trường thực thi:**
   - Python 3.12+ với `uv`, `PySide6`, `pytest`, `pytest-qt`.
   - Biến môi trường chạy test headless: `QT_QPA_PLATFORM=offscreen`.
2. **Dữ liệu Cấu hình & Từ điển:**
   - Module `labelme/_medical_terminology.py` nạp sẵn bộ nhãn mặc định `chest_xray` gồm đúng **21 bệnh lý** chia làm **4 nhóm giải phẫu**:
     1. `lung_parenchyma` (*Lung parenchyma* / *Nhu mô phổi*) — 11 nhãn.
     2. `pleura` (*Pleura* / *Màng phổi*) — 5 nhãn.
     3. `hilum_mediastinum` (*Hilum / Mediastinum* / *Rốn phổi / trung thất*) — 3 nhãn.
     4. `heart_diaphragm_trachea` (*Heart / Diaphragm / Trachea* / *Tim / cơ hoành / khí quản*) — 2 nhãn.
   - File dịch `labelme/translate/vi_VN.qm` đã được biên dịch từ `vi_VN.ts`.

______________________________________________________________________

## 3. Định Danh Tương Tác & Cấu Trúc Dữ Liệu (Automation Hooks & Data Contracts)

### 3.1. Bảng Định Danh Widget (`objectName` / `accessibleName` / Thuộc tính Public)

| Tầng / Màn hình | Tên Class / File | Định danh (`objectName` / Thuộc tính) | Vai trò & Hành vi |
| :--- | :--- | :--- | :--- |
| **Terminology Engine** | `labelme/_medical_terminology.py` | `CHEST_XRAY_PRESET`, `TerminologyItem`, `TerminologyPreset`, `MedicalTerminologyRegistry` | Quản lý bộ nhãn mặc định, bộ nhãn tùy chỉnh, tra cứu tên hiển thị Full/Short theo locale (`en_US` / `vi_VN`), tra cứu màu RGB và phân giải mã chuẩn Tiếng Anh. |
| **Bảng Label List (Dock phải)** | `UniqueLabelQListWidget` (`_unique_label_qlist_widget.py`) | `preset_combo` (`objectName="preset_combo"`), `category_combo` (`objectName="category_combo"`), `add_label_button` (`objectName="add_label_button"`) | Cho phép chọn Bộ nhãn (Preset), lọc danh sách theo Nhóm giải phẫu, và bấm nút `+` để mở Form thêm nhãn mới. |
| **Hộp thoại Chọn Nhãn (Popup)** | `LabelDialog` (`_label_dialog.py`) | `category_combo` (`objectName="category_combo"`), `add_label_button` (`objectName="add_label_button"`), `edit`, `edit_group_id`, `label_list` | Lọc theo Nhóm giải phẫu, gõ tìm kiếm lọc trực tiếp theo từ khóa (EN/VI/Aliases), hiển thị tên rút gọn khi lọc Nhóm, trả về `LabelDialogEntry.label` là mã chuẩn Tiếng Anh. |
| **Form Thêm Nhãn Mới** | `MedicalLabelFormDialog` (`_medical_label_dialog.py`) | `english_label_edit` (`objectName="english_label_edit"`), `vietnamese_label_edit` (`objectName="vietnamese_label_edit"`), `short_english_edit`, `short_vietnamese_edit`, `category_combo` (`objectName="category_combo"`), `color_button`, `error_label` | Kiểm tra hợp lệ: bắt buộc có Mã chuẩn Tiếng Anh (ASCII/English), không trùng lặp, chọn hoặc nhập Nhóm, chọn màu RGB. |
| **Form Tạo Bộ Nhãn Mới** | `MedicalPresetFormDialog` (`_medical_label_dialog.py`) | `preset_name_edit` (`objectName="preset_name_edit"`), `error_label` | Tạo bộ nhãn (Preset) mới qua Form UI để bác sĩ chuyển đổi giữa các chuyên khoa. |

### 3.2. Cấu Trúc Lưu Trữ File Kết Quả `.json` (JSON Annotation Contract)

Dù giao diện đang ở Tiếng Việt (`vi_VN`) hay đang lọc theo Nhóm hiển thị rút gọn (`Đám mờ` / `Opacity`), cấu trúc file `.json` lưu xuống đĩa bắt buộc tuân thủ:

```json
{
  "version": "7.12.0",
  "flags": {},
  "shapes": [
    {
      "label": "Lung opacity",
      "points": [[100.0, 120.0], [220.0, 260.0]],
      "group_id": null,
      "description": "",
      "shape_type": "rectangle",
      "flags": {},
      "mask": null
    }
  ],
  "imagePath": "chest_xray_01.dcm",
  "imageData": null,
  "imageHeight": 1024,
  "imageWidth": 1024
}
```

______________________________________________________________________

## 4. Kịch Bản Kiểm Thử Hộp Xám (Grey-box Test Cases)

### `TC-01`: Khởi động mặc định nạp sẵn 21 nhãn X-quang ngực (`chest_xray`) và bảng màu chuẩn

- **Luồng thực thi:**
  1. Khởi tạo `MainWindow` với cấu hình mặc định (`default_config.yaml`).
  2. Kiểm tra danh sách nhãn trong `win._docks.unique_label_list.labels()` và `win._label_dialog`.
- **Xác minh Hộp xám (Grey-box State):**
  - `unique_label_list.labels()` chứa đúng 21 mã chuẩn Tiếng Anh theo đúng thứ tự 4 nhóm giải phẫu (bắt đầu từ `"Lung opacity"`, kết thúc ở `"Tracheal shift"`).
  - Mỗi item trong `unique_label_list` có `item.data(Qt.ItemDataRole.UserRole)` là mã chuẩn Tiếng Anh và `item.data(LABEL_COLOR_ROLE)` khớp với bảng màu y khoa của nhãn đó.

### `TC-02`: Hiển thị theo ngôn ngữ Giao diện (Tiếng Việt vs Tiếng Anh) khi xem "Tất cả (All)"

- **Luồng thực thi:**
  1. Ở chế độ ngôn ngữ Tiếng Anh (`en_US`), kiểm tra `item.text()` của nhãn `"Lung opacity"` và `"Pleural calcification"` trong `UniqueLabelQListWidget` và `LabelDialog` khi bộ lọc nhóm ở trạng thái `"All"`.
  2. Cài đặt `QTranslator` với `vi_VN.qm` (hoặc cấu hình locale `vi_VN`), kiểm tra lại `item.text()`.
- **Xác minh Hộp xám (Grey-box State):**
  - Khi locale = `en_US`: Hiển thị tên đầy đủ Tiếng Anh `"Lung opacity"` và `"Pleural calcification"`.
  - Khi locale = `vi_VN`: Hiển thị tên đầy đủ Tiếng Việt `"Đám mờ phổi"` và `"Vôi hóa màng phổi"`.
  - Trong cả 2 ngôn ngữ, `item.data(Qt.ItemDataRole.UserRole)` luôn bất biến là `"Lung opacity"` và `"Pleural calcification"`.

### `TC-03`: Hiển thị Rút gọn theo Ngữ cảnh Nhóm (`Context-Aware Short Display`)

- **Luồng thực thi:**
  1. Mở `LabelDialog` (hoặc trên `UniqueLabelQListWidget`).
  2. Chọn bộ lọc nhóm `category_combo` sang nhóm **Nhu mô phổi (`Lung parenchyma`)**.
  3. Kiểm tra danh sách các dòng đang hiển thị (visible items).
  4. Chuyển bộ lọc nhóm sang **Màng phổi (`Pleura`)**, kiểm tra danh sách hiển thị.
  5. Chuyển bộ lọc nhóm về **Tất cả (`All`)**, kiểm tra lại.
- **Xác minh Hộp xám (Grey-box State):**
  - Khi chọn nhóm **Nhu mô phổi**:
    - Chỉ có đúng 11 dòng thuộc nhóm Nhu mô phổi hiển thị (các nhóm khác bị ẩn).
    - Tên hiển thị của `"Lung opacity"` được rút gọn thành `"Opacity"` (khi UI = EN) hoặc `"Đám mờ"` (khi UI = VI).
    - Tên hiển thị của `"Pulmonary nodule"` được rút gọn thành `"Nodule"` (EN) hoặc `"Nốt"` (VI).
    - Tên hiển thị của `"Pulmonary mass"` được rút gọn thành `"Mass"` (EN) hoặc `"Khối"` (VI).
  - Khi chọn nhóm **Màng phổi**:
    - Chỉ có đúng 5 dòng thuộc nhóm Màng phổi hiển thị.
    - `"Pleural effusion"` hiển thị rút gọn là `"Effusion"` (EN) hoặc `"Tràn dịch"` (VI).
    - `"Pleural calcification"` hiển thị rút gọn là `"Calcification"` (EN) hoặc `"Vôi hóa"` (VI), nhưng khi chọn dòng này thì `UserRole` trả về đúng `"Pleural calcification"` (không bị nhầm sang `"Calcification"` của Nhu mô phổi!).
  - Khi quay về **Tất cả (`All`)**: Tất cả 21 nhãn hiển thị lại tên đầy đủ (`"Lung opacity"`, `"Pleural calcification"`).

### `TC-04`: Chọn nhãn trên UI Tiếng Việt / Rút gọn nhưng Lưu File `.json` 100% Chuẩn Tiếng Anh

- **Luồng thực thi:**
  1. Bật giao diện Tiếng Việt (`vi_VN`).
  2. Vẽ một vùng bệnh trên `Canvas`, khi `LabelDialog` bật lên, chọn nhóm `"Nhu mô phổi"`, nhấp đúp (double-click) vào dòng `"Đám mờ"`.
  3. Lưu file chú thích ra đĩa (`tmp_path / "test_case.json"`).
- **Xác minh Hộp xám (Grey-box State):**
  - Đối tượng `canvas.shapes[0].label` trong RAM có giá trị `"Lung opacity"`.
  - Trên bảng `Shape List` (`win._docks.label_list`), dòng hình vẽ hiển thị tên Tiếng Việt đầy đủ `"Đám mờ phổi"`.
  - Đọc nội dung file `test_case.json` trên đĩa cứng: `json.loads(...)["shapes"][0]["label"] == "Lung opacity"`.

### `TC-05`: Tìm kiếm thông minh qua Từ khóa & Từ đồng nghĩa (Search & Aliases Filtering)

- **Luồng thực thi:**
  1. Mở `LabelDialog` với bộ nhãn `chest_xray`.
  2. Gõ từ khóa `"collapse"` (từ đồng nghĩa của `Atelectasis`) hoặc `"deviation"` (từ đồng nghĩa của `Tracheal shift`) hoặc `"đông đặc"` (tiếng Việt) vào ô `edit`.
- **Xác minh Hộp xám (Grey-box State):**
  - Danh sách `label_list` tự động lọc/chọn đúng dòng `"Atelectasis"` / `"Tracheal shift"` / `"Consolidation"`.
  - Khi nhấn `Enter` hoặc bấm `OK`, nhãn trả về trong `LabelDialogEntry.label` là mã chuẩn Tiếng Anh tương ứng (`"Atelectasis"`, `"Tracheal shift"`, `"Consolidation"`).

### `TC-06`: Bổ sung Nhãn mới qua Form UI (`MedicalLabelFormDialog`) — Luồng Hợp lệ

- **Luồng thực thi:**
  1. Bấm nút `add_label_button` (`+`) trên `UniqueLabelQListWidget` (hoặc trong `LabelDialog`) để mở `MedicalLabelFormDialog`.
  2. Nhập:
     - `english_label_edit`: `"Rib fracture"`
     - `vietnamese_label_edit`: `"Gãy xương sườn"`
     - `short_english_edit`: `"Fracture"`
     - `short_vietnamese_edit`: `"Gãy"`
     - `category_combo`: Chọn `"Pleura"` (hoặc nhập nhóm mới `"Chest wall"`).
  3. Bấm `OK` để lưu.
- **Xác minh Hộp xám (Grey-box State):**
  - Nhãn `"Rib fracture"` xuất hiện ngay trong `UniqueLabelQListWidget` và `LabelDialog` kèm màu đã chọn.
  - Khi UI ở Tiếng Việt, nhãn hiển thị là `"Gãy xương sườn"` (và hiển thị `"Gãy"` khi lọc riêng nhóm đó), nhưng khi gán vào hình vẽ và lưu JSON thì lưu `"Rib fracture"`.
  - Cấu hình `custom_terminologies` được ghi bền vững vào file cấu hình (`~/.labelmerc`) để lần sau mở phần mềm vẫn còn.

### `TC-07`: Kiểm tra Chốt chặn Dữ liệu trên Form Thêm Nhãn (`Validation Errors`)

- **Luồng thực thi:**
  1. Mở `MedicalLabelFormDialog`.
  2. Trường hợp A: Để trống `english_label_edit` và bấm `OK`.
  3. Trường hợp B: Nhập tiếng Việt có dấu `"Gãy xương"` vào ô `english_label_edit` (ô dành cho mã chuẩn Tiếng Anh AI).
  4. Trường hợp C: Nhập `"lung opacity"` (trùng với nhãn đã có sẵn) vào `english_label_edit`.
- **Xác minh Hộp xám (Grey-box State):**
  - Trong cả 3 trường hợp, Form **không đóng lại**, `error_label.isVisible() == True`, hiển thị thông báo lỗi rõ ràng và không ghi dữ liệu rác vào Registry hay file cấu hình.

### `TC-08`: Chuyển đổi Bộ nhãn (`Preset Switcher`) & Tạo Bộ nhãn Mới qua Form UI

- **Luồng thực thi:**
  1. Trên `UniqueLabelQListWidget`, kiểm tra `preset_combo` đang chọn `"chest_xray"` (21 nhãn).
  2. Tạo một bộ nhãn mới qua `MedicalPresetFormDialog` (ví dụ: `"Brain CT"`), thêm nhãn `"Intracranial hemorrhage"` (*Xuất huyết nội sọ*).
  3. Dùng `preset_combo` chuyển qua lại giữa `"Chest X-Ray"` và `"Brain CT"`.
- **Xác minh Hộp xám (Grey-box State):**
  - Khi chọn `"Brain CT"`, bảng `Label List` và `LabelDialog` cập nhật sang danh sách nhãn và nhóm của `"Brain CT"`.
  - Các hình vẽ (Shapes) của ảnh hiện tại đã vẽ trước đó vẫn giữ nguyên nhãn và không bị mất dữ liệu.
  - Khi chuyển lại `"Chest X-Ray"`, 21 nhãn phổi và 4 nhóm giải phẫu hiển thị lại đầy đủ.

### `TC-09`: Luồng "Chọn nhãn trước ở bảng bên phải -> Khoanh liên tiếp trên phim"

- **Luồng thực thi:**
  1. Bác sĩ lọc nhóm `"Màng phổi"` trên bảng `UniqueLabelQListWidget` bên phải, click chọn dòng `"Tràn dịch"` (`"Pleural effusion"`).
  2. Tắt `display_label_popup` (`False`), vẽ 1 hình chữ nhật trên Canvas.
- **Xác minh Hộp xám (Grey-box State):**
  - Hình vẽ mới được tạo ngay lập tức mà không bật popup, và `shape.label` nhận đúng mã chuẩn Tiếng Anh `"Pleural effusion"` (không bị lấy chuỗi hiển thị rút gọn `"Tràn dịch"`).

### `TC-10`: Tương thích ngược 100% với bộ Unit & E2E Tests hiện có của Labelme

- **Luồng thực thi:**
  1. Chạy toàn bộ bộ test hiện tại của dự án (`uv run pytest -v tests/`) và kiểm tra lint/translation (`just lint`, `just check_translate`).
- **Xác minh Hộp xám (Grey-box State):**
  - 100% bài test cũ (bao gồm `tests/unit/widgets/_label_dialog/`, `tests/unit/widgets/_unique_label_qlist_widget_test.py`, `tests/e2e/`) và bộ test mới cho Medical Terminology đều **PASS 100%**.
