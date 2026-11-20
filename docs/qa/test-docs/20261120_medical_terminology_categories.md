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
| **Bảng Label List (Dock phải) & Popup Chọn Nhãn** | `UniqueLabelQListWidget` (\[`_unique_label_qlist_widget.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_unique_label_qlist_widget.py)), `LabelDialog` (\[`_label_dialog.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_label_dialog.py)) | `category_combo`, `add_label_button` (`+`), `edit_label_button` (`✎`, `objectName="edit_label_button"`), `delete_label_button` (`-`, `objectName="delete_label_button"`) | Cho phép Thêm (`+`), Sửa (`✎` hoặc menu chuột phải `Edit Medical Label…`), Xóa (`-` hoặc menu chuột phải `Delete Medical Label`) bất kỳ nhãn nào (kể cả 21 nhãn preset). Chuột phải trên `category_combo` cũng cho phép Thêm/Sửa/Xóa nhóm. |
| **Form Thêm / Sửa Nhãn** | `MedicalLabelFormDialog` (\[`_medical_label_dialog.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_medical_label_dialog.py)) | `category_combo` (`objectName="category_combo"`), `add_category_button` (`+`), `edit_category_button` (`✎`, `objectName="edit_category_button"`), `delete_category_button` (`-`, `objectName="delete_category_button"`), `editing_item` | Hỗ trợ cả 2 chế độ: **Add Medical Label** và **Edit Medical Label**. Dòng `Anatomical Category:` có đủ 3 nút `+` (Thêm nhóm), `✎` (Sửa nhóm đang chọn), `-` (Xóa nhóm đang chọn). |
| **Hộp thoại Thêm / Sửa Nhóm** | `MedicalCategoryFormDialog` (\[`_medical_label_dialog.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_widgets/\_medical_label_dialog.py)) | `english_category_edit` (`objectName="english_category_edit"`), `vietnamese_category_edit` (`objectName="vietnamese_category_edit"`), `error_label` (`objectName="error_label"`), `ok_button`, `cancel_button`, `editing_category`, `created_category` | Hỗ trợ cả 2 chế độ: **Add Anatomical Category** và **Edit Anatomical Category**. Khi ở chế độ Edit, nạp sẵn `en_name` và `vi_name` hiện tại của nhóm để bác sĩ chỉnh sửa. |
| **Terminology Engine** | `MedicalTerminologyRegistry` (\[`_medical_terminology.py`\](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/\_medical_terminology.py)) | `add_custom_category`, `update_category`, `delete_category`, `add_custom_label`, `update_label`, `delete_label` | Thực thi CRUD toàn diện cho cả dữ liệu tự thêm lẫn dữ liệu Preset mặc định (`chest_xray`), lưu và khôi phục bền vững trong `custom_terminologies` (`~/.labelmerc`). |

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

### `TC-15`: Tự động kết nối bộ gõ Tiếng Việt Fcitx5 qua IBus Portal trên Linux (`_configure_linux_input_method`)

- **Luồng thực thi:**
  1. Giả lập môi trường Linux có `QT_IM_MODULE="fcitx"` (hoặc `"fcitx5"`, hoặc `XMODIFIERS="@im=fcitx"`) khi thư mục `platforminputcontexts` của PySide6 chỉ có `libibusplatforminputcontextplugin.so` mà không có `libfcitx5platforminputcontextplugin.so`.
  2. Gọi hàm `_configure_linux_input_method()` trước khi khởi tạo `QApplication`.
- **Xác minh Hộp xám (Grey-box State):**
  - `os.environ["QT_IM_MODULE"]` được tự động chuyển sang `"ibus"` và `os.environ["IBUS_USE_PORTAL"] == "1"` để Qt 6 kết nối trực tiếp vào dịch vụ `org.freedesktop.portal.IBus` của Fcitx5 thay vì rơi về `compose`.

### `TC-16`: Gõ Tiếng Việt có dấu (IME Preedit / Commit, NFC & NFD) và Không bị `InlineCompletion` nuốt chữ trên `LabelDialog.edit` & các ô Localized Input

- **Luồng thực thi:**
  1. Mở `LabelDialog` với bộ nhãn `chest_xray` ở giao diện Tiếng Việt (`vi_VN`) và `completion="startswith"`, focus vào `dialog.edit`.
  2. Gõ phím `"D"` hoặc `"T"` hoặc gửi chuỗi sự kiện IME (`QInputMethodEvent` với `preeditString="Đám"`, sau đó commit `"Đám mờ"`).
  3. Mở `MedicalLabelFormDialog` và `MedicalCategoryFormDialog`, nhập/gửi sự kiện IME Tiếng Việt có dấu (cả dạng dựng sẵn NFC lẫn tổ hợp NFD) vào `vietnamese_label_edit`, `short_vietnamese_edit`, `vietnamese_category_edit`.
- **Xác minh Hộp xám (Grey-box State):**
  - Khi gõ `"D"` vào `dialog.edit` đang focus: `InlineCompletion` **không** tự ý biến chữ trong `dialog.edit` thành `"Dày màng phổi"` làm ẩn mất `"Đám mờ phổi"`, `"Đông đặc phổi"`, `"Di lệch khí quản"`; tất cả các nhãn có chứa `"d"` / `"đ"` vẫn hiển thị đầy đủ để người dùng gõ tiếp dấu Tiếng Việt.
  - Khi đang gõ dở ở trạng thái gạch chân IME (`QInputMethodEvent` với `preeditString="Đám"`): `dialog.visible_labels()` lọc tức thời ra `["Lung opacity"]` (*Đám mờ phổi*) và nút `OK` được bật.
  - Trên các ô `vietnamese_label_edit`, `short_vietnamese_edit`, `vietnamese_category_edit`: Nhận đầy đủ chuỗi Tiếng Việt có dấu và tự động chuẩn hóa về Unicode `NFC`.

### `TC-17`: Chỉnh sửa Nhãn Y Khoa (`Edit Medical Label`) — Kể cả Nhãn Preset & Đồng bộ Hình vẽ (`Shape`) trên Ảnh Hiện tại

- **Luồng thực thi:**
  1. Khởi tạo `MainWindow`, vẽ 1 hình chữ nhật mang nhãn `"Lung opacity"` (*Đám mờ phổi*) trên Canvas.
  2. Chọn dòng `"Lung opacity"` trên `UniqueLabelQListWidget` (hoặc trên `LabelDialog`), bấm nút `edit_label_button` (`✎`) để mở `MedicalLabelFormDialog` ở chế độ **Edit Medical Label**.
  3. Kiểm tra form nạp sẵn 6 trường của `"Lung opacity"`. Sửa `english_label_edit = "Pulmonary infiltrate"`, `vietnamese_label_edit = "Thâm nhiễm phổi"`, `short_english_edit = "Infiltrate"`, `short_vietnamese_edit = "Thâm nhiễm"`, màu `(255, 100, 50)`, bấm `OK`.
- **Xác minh Hộp xám (Grey-box State):**
  - Nhãn `"Lung opacity"` tại vị trí đầu tiên trong Registry được cập nhật thành `"Pulmonary infiltrate"` (*Thâm nhiễm phổi*).
  - Hình vẽ đang có trên Canvas tự động cập nhật `canvas.shapes[0].label == "Pulmonary infiltrate"` và dòng trên `Shape List` hiển thị `"Thâm nhiễm phổi"` (khi UI ở Tiếng Việt).
  - Sau khi đóng và mở lại `MainWindow` với cùng `~/.labelmerc`, nhãn đã sửa `"Pulmonary infiltrate"` vẫn giữ nguyên (nhãn cũ `"Lung opacity"` không tự xuất hiện lại).

### `TC-18`: Xóa Nhãn Y Khoa (`Delete Medical Label`) có Hộp thoại Xác nhận (`Yes / No Confirmation`) — Kể cả Nhãn Preset

- **Luồng thực thi:**
  1. Khởi tạo `MainWindow` với 21 nhãn mặc định.
  2. Chọn nhãn `"Tracheal shift"` (nhãn preset) trên `UniqueLabelQListWidget`, bấm nút `delete_label_button` (`-`).
  3. Trong hộp thoại xác nhận `QMessageBox` (*Delete Medical Label*) bật lên lần 1: bấm **`No`**.
  4. Bấm lại nút `delete_label_button` (`-`), trong hộp thoại xác nhận `QMessageBox` bật lên lần 2: bấm **`Yes`**.
- **Xác minh Hộp xám (Grey-box State):**
  - Ở bước 3 (khi bấm **`No`**): Nhãn `"Tracheal shift"` **không bị xóa**, danh sách vẫn giữ nguyên `21` nhãn.
  - Ở bước 4 (khi bấm **`Yes`**): Số lượng nhãn trong `registry.canonical_labels()` và `unique_list.settings_labels()` giảm từ `21` xuống `20`, `"Tracheal shift"` không còn trong danh sách.
  - Sau khi đóng và mở lại `MainWindow` với cùng `~/.labelmerc`, `"Tracheal shift"` vẫn bị xóa (`len(reopened._docks.unique_label_list.settings_labels()) == 20`).

### `TC-19`: Chỉnh sửa Nhóm Giải Phẫu (`Edit Anatomical Category`) — Kể cả Nhóm Preset & Cập nhật Đồng bộ các Nhãn thuộc Nhóm

- **Luồng thực thi:**
  1. Mở `MedicalLabelFormDialog`, chọn nhóm `"Pleura"` (*Màng phổi*), bấm nút `edit_category_button` (`✎`) để mở `MedicalCategoryFormDialog` ở chế độ **Edit Anatomical Category**.
  2. Sửa `english_category_edit = "Pleural space"`, `vietnamese_category_edit = "Khoang màng phổi"`, bấm `OK`.
- **Xác minh Hộp xám (Grey-box State):**
  - Nhóm `"pleura"` trong Registry được cập nhật thành `category_id == "pleural_space"`, `en_name == "Pleural space"`, `vi_name == "Khoang màng phổi"`.
  - Cả 5 nhãn thuộc nhóm màng phổi (*Pleural effusion*, *Pleural thickening*...) đều tự động cập nhật `category_id == "pleural_space"`, `category_en == "Pleural space"`, `category_vi == "Khoang màng phổi"`.
  - Các dropdown lọc nhóm trên `UniqueLabelQListWidget` và `LabelDialog` hiển thị `"Pleural space"` (EN) / `"Khoang màng phổi"` (VI) và lọc đúng 5 nhãn đó.
  - Khởi động lại `MainWindow` vẫn bảo toàn tên nhóm mới.

### `TC-20`: Xóa Nhóm Giải Phẫu (`Delete Anatomical Category`) có Hộp thoại Xác nhận (`Yes / No Confirmation`) — Kể cả Nhóm Preset

- **Luồng thực thi:**
  1. Mở `MedicalLabelFormDialog`, chọn nhóm `"Heart / Diaphragm / Trachea"` (gồm 2 nhãn *Cardiomegaly* và *Tracheal shift*), bấm nút `delete_category_button` (`-`).
  2. Trong hộp thoại xác nhận `QMessageBox` (*Delete Anatomical Category*, hiển thị rõ số lượng 2 nhãn bên trong) bật lên lần 1: bấm **`No`**.
  3. Bấm lại nút `delete_category_button` (`-`), trong hộp thoại xác nhận `QMessageBox` bật lên lần 2: bấm **`Yes`**.
- **Xác minh Hộp xám (Grey-box State):**
  - Ở bước 2 (khi bấm **`No`**): Nhóm `"Heart / Diaphragm / Trachea"` và 2 nhãn bên trong **không bị xóa** (`4` nhóm, `21` nhãn).
  - Ở bước 3 (khi bấm **`Yes`**): Số lượng nhóm trong `registry.categories()` giảm từ `4` xuống `3`, nhóm `"heart_diaphragm_trachea"` và 2 nhãn thuộc nhóm đó bị xóa khỏi `preset.categories` và `preset.items` (còn `19` nhãn).
  - Sau khi đóng và mở lại `MainWindow` với cùng `~/.labelmerc`, hệ thống vẫn giữ đúng `3` nhóm và `19` nhãn.
