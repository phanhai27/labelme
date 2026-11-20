# Đặc Tả Kiểm Thử Hộp Xám (QA Test Docs / ATDD Contract): Hộp Thoại Thêm Nhóm Giải Phẫu (`Add Anatomical Category`)

- **Mã tài liệu:** `20261120_medical_terminology_categories.md`
- **Ngày lập:** `2026-11-20`
- **Phạm vi kiểm thử:** Desktop Application (`PySide6` / `pytest-qt` Unit & Integration Tests)

______________________________________________________________________

## 1. Ngữ Cảnh & Mục Tiêu (Context & Rationale)

- **Tại sao tính năng này tồn tại?**
  - Khi bác sĩ mở hộp thoại **Add Medical Label (`MedicalLabelFormDialog`)**, ô chọn **Anatomical Category** trước đây chỉ hiển thị 4 nhóm mặc định (*Lung parenchyma*, *Pleura*, *Hilum / Mediastinum*, *Heart / Diaphragm / Trachea*) mà không có nút bấm hay mục chọn trực quan để thêm nhóm giải phẫu mới.
  - Hệ thống cần cung cấp nút **`+` (`add_category_button`)** bên cạnh dropdown `Anatomical Category` (và dòng **`+ Add New Category…`** ngay trong dropdown) để bật hộp thoại nhỏ **`Add Anatomical Category` (`MedicalCategoryFormDialog`)**.
  - Đảm bảo 2 nguyên tắc cốt lõi của Labelme:
    1. **Nhãn và định danh cho AI lấy Tiếng Anh làm chuẩn (`Canonical English`)**: Tên chuẩn Tiếng Anh của nhóm (`en_name`) và nhãn (`canonical_label`) bắt buộc là ASCII Tiếng Anh không dấu.
    2. **Localized Text cho giao diện địa phương**: Nhóm mới hỗ trợ nhập `Localized Display Name` (`vi_name`) để khi giao diện chạy Tiếng Việt (`vi_VN`), cả dropdown trong form lẫn thanh lọc nhóm bên ngoài đều hiển thị tên Tiếng Việt, còn khi chạy Tiếng Anh (`en_US`) thì hiển thị tên Tiếng Anh.

______________________________________________________________________

## 2. Tiền Điều Kiện (Preconditions)

1. **Môi trường thực thi:** Python 3.12+, `uv`, `PySide6`, `pytest`, `pytest-qt` (`QT_QPA_PLATFORM=offscreen`).
2. **Dữ liệu mặc định:** Bộ nhãn `chest_xray` giữ nguyên **4 nhóm giải phẫu mặc định** và **21 nhãn bệnh lý**.

______________________________________________________________________

## 3. Định Danh Tương Tác & Cấu Trúc Dữ Liệu (Automation Hooks & Data Contracts)

### 3.1. Bảng Định Danh Widget (`objectName` / Thuộc tính Public)

| Tầng / Hộp thoại | Tên Class / File | Định danh (`objectName` / Thuộc tính) | Vai trò & Hành vi |
| :--- | :--- | :--- | :--- |
| **Form Thêm Nhãn** | `MedicalLabelFormDialog` (\[`_medical_label_dialog.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_medical_label_dialog.py)) | `category_combo` (`objectName="category_combo"`), `add_category_button` (`objectName="add_category_button"`) | `category_combo` liệt kê 4 nhóm mặc định (hiển thị theo ngôn ngữ UI) + dòng cuối `+ Add New Category…` (`NEW_CATEGORY_SENTINEL = "__new_category__"`). Nút `+` (`add_category_button`) nằm ngay bên phải `category_combo` để mở `MedicalCategoryFormDialog`. |
| **Hộp thoại Thêm Nhóm** | `MedicalCategoryFormDialog` (\[`_medical_label_dialog.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_medical_label_dialog.py)) | `english_category_edit` (`objectName="english_category_edit"`), `vietnamese_category_edit` (`objectName="vietnamese_category_edit"`), `error_label` (`objectName="error_label"`), `ok_button`, `cancel_button`, `created_category` | Kiểm tra hợp lệ: bắt buộc có `Canonical English Category *` (ASCII Tiếng Anh, không dấu, không trùng lặp) và tùy chọn `Localized Display Name`. Khi bấm `OK`, tạo `TerminologyCategory` mới trong Registry. |
| **Terminology Engine** | `MedicalTerminologyRegistry` (\[`_medical_terminology.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_medical_terminology.py)) | `add_custom_category(en_name, vi_name, preset_id)`, `validate_canonical_english_category(...)` | Kiểm tra hợp lệ, sinh `category_id` từ `en_name`, thêm nhóm vào preset hiện hành và lưu cấu hình bền vững vào `custom_terminologies.added_categories`. |

### 3.2. Cấu Trúc Lưu Trữ Cấu Hình `~/.labelmerc` (`custom_terminologies`)

```yaml
label_preset: chest_xray
custom_terminologies:
  added_categories:
    chest_xray:
      - category_id: chest_wall_bones
        en_name: Chest wall / Bones
        vi_name: Thành ngực / Xương
  added_items:
    chest_xray:
      - canonical_label: Rib fracture
        en_full: Rib fracture
        en_short: Fracture
        vi_full: Gãy xương sườn
        vi_short: Gãy
        category_id: chest_wall_bones
        category_en: Chest wall / Bones
        category_vi: Thành ngực / Xương
        color: [250, 128, 114]
        aliases: [rib fracture, fracture, gãy xương sườn, gãy, gay xuong suon, gay]
```

______________________________________________________________________

## 4. Kịch Bản Kiểm Thử Hộp Xám (Grey-box Test Cases)

### `TC-11`: Mở hộp thoại `Add Anatomical Category` từ nút `+` (`add_category_button`) và tạo nhóm mới thành công

- **Luồng thực thi:**
  1. Mở `MedicalLabelFormDialog` (`Add Medical Label`).
  2. Kiểm tra số lượng nhóm mặc định trong `registry.categories()` là `4` nhóm, và `add_category_button` hiển thị bên cạnh `category_combo`.
  3. Bấm nút `add_category_button` (`+`) để bật hộp thoại con `MedicalCategoryFormDialog` (`Add Anatomical Category`).
  4. Nhập `english_category_edit = "Chest wall / Bones"`, `vietnamese_category_edit = "Thành ngực / Xương"`, bấm `OK`.
- **Xác minh Hộp xám (Grey-box State):**
  - `registry.categories()` tăng từ `4` lên `5` nhóm, nhóm thứ 5 có `category_id == "chest_wall_bones"`, `en_name == "Chest wall / Bones"`, `vi_name == "Thành ngực / Xương"`.
  - Trên `MedicalLabelFormDialog`, `category_combo.currentData() == "chest_wall_bones"`, hiển thị `"Chest wall / Bones"` khi UI ở Tiếng Anh và `"Thành ngực / Xương"` khi UI ở Tiếng Việt.
  - Cấu hình `custom_terminologies["added_categories"]["chest_xray"]` được ghi bền vững vào `~/.labelmerc`.

### `TC-12`: Mở hộp thoại `Add Anatomical Category` khi chọn dòng `+ Add New Category…` trong dropdown `category_combo` (và xử lý khi bấm `Cancel`)

- **Luồng thực thi:**
  1. Mở `MedicalLabelFormDialog`, lúc này `category_combo` đang chọn nhóm `"Pleura"` (`category_id == "pleura"`).
  2. Chọn mục cuối cùng `+ Add New Category…` (`NEW_CATEGORY_SENTINEL`) trong `category_combo`.
  3. Trong hộp thoại `MedicalCategoryFormDialog` bật lên, bấm `Cancel` (`reject()`).
  4. Chọn lại mục `+ Add New Category…`, lần này nhập `english_category_edit = "Medical devices"`, `vietnamese_category_edit = "Thiết bị y tế"` và bấm `OK`.
- **Xác minh Hộp xám (Grey-box State):**
  - Ở bước 3 (khi bấm `Cancel`): Không có nhóm mới nào được tạo (`len(registry.categories()) == 4`), và `category_combo` tự động quay về nhóm đang chọn trước đó là `"Pleura"` (`currentData() == "pleura"`).
  - Ở bước 4 (khi bấm `OK`): Nhóm `"Medical devices"` (`category_id == "medical_devices"`) được tạo và `category_combo.currentData() == "medical_devices"`.

### `TC-13`: Kiểm tra Chốt chặn Dữ liệu trên hộp thoại `Add Anatomical Category` (`Validation Errors`)

- **Luồng thực thi:**
  1. Mở `MedicalCategoryFormDialog`.
  2. Trường hợp A: Để trống `english_category_edit` (`"   "`) và bấm `OK`.
  3. Trường hợp B: Nhập tiếng Việt có dấu `"Thành ngực"` vào ô `english_category_edit` (ô bắt buộc Tiếng Anh chuẩn) và bấm `OK`.
  4. Trường hợp C: Nhập tên trùng với nhóm đã có sẵn `"pleura"` (hoặc `"Màng phổi"`) và bấm `OK`.
- **Xác minh Hộp xám (Grey-box State):**
  - Trong cả 3 trường hợp, hộp thoại `MedicalCategoryFormDialog` **không đóng lại**, `error_label.isVisible() == True`, thông báo lỗi rõ ràng, và `len(registry.categories())` vẫn giữ nguyên là `4`.

### `TC-14`: Hiển thị Localized Text cho Nhóm mới và Lưu JSON Chuẩn Tiếng Anh cho AI

- **Luồng thực thi:**
  1. Bật giao diện Tiếng Việt (`vi_VN.qm`).
  2. Mở `MedicalLabelFormDialog`, bấm `add_category_button` để tạo nhóm mới `en_name="Chest wall / Bones"`, `vi_name="Thành ngực / Xương"`.
  3. Thêm nhãn mới `english_label_edit="Rib fracture"`, `vietnamese_label_edit="Gãy xương sườn"`, `short_english_edit="Fracture"`, `short_vietnamese_edit="Gãy"` vào nhóm vừa tạo và bấm `OK`.
  4. Kiểm tra thanh lọc nhóm `category_combo` trên `UniqueLabelQListWidget` và `LabelDialog`, chọn lọc theo nhóm `"Thành ngực / Xương"`, gán nhãn cho hình vẽ và lưu ra file `.json`.
- **Xác minh Hộp xám (Grey-box State):**
  - Khi UI ở Tiếng Việt: Dropdown lọc nhóm hiển thị `"Thành ngực / Xương"`; khi lọc vào nhóm này, nhãn hiển thị rút gọn là `"Gãy"`; khi xem `"Tất cả"`, nhãn hiển thị `"Gãy xương sườn"`.
  - Khi UI ở Tiếng Anh: Dropdown lọc nhóm hiển thị `"Chest wall / Bones"`; khi lọc vào nhóm này, nhãn hiển thị rút gọn là `"Fracture"`; khi xem `"All"`, nhãn hiển thị `"Rib fracture"`.
  - Trong file `.json` xuất ra cho AI: `shapes[0]["label"]` luôn là `"Rib fracture"`.
