# Tài liệu Đặc tả Kiểm thử (ATDD / Grey-Box Contract): Nâng cấp Tương tác Canvas & DICOM Ergonomics (`Labelme`)

- **Ngày lập**: `2026-11-18`
- **Phạm vi**: Desktop App `labelme` (PySide6) — [`labelme/_app.py`](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/_app.py), [`labelme/_widgets/_canvas.py`](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/_widgets/_canvas.py), [`labelme/_config/default_config.yaml`](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/_config/default_config.yaml), [`labelme/_dicom.py`](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/_dicom.py).

---

## 1. Ngữ cảnh & Mục tiêu (Context & Rationale)

Bản nâng cấp này giải quyết triệt để rào cản thao tác khi Bác sĩ Chẩn đoán Hình ảnh và Chuyên viên gán nhãn làm việc trên các lát cắt CT/MRI DICOM và ảnh 2D độ phân giải cao:
1. Chuẩn hóa **Focal Wheel Zoom** (lăn chuột phóng to/thu nhỏ trực tiếp tại trỏ chuột) và **`Shift + Wheel`** lướt lát cắt.
2. Cung cấp **công cụ Bàn tay `Pan (H)`** trên thanh công cụ trái và **Spring-loaded Hand Pan (`Giữ Space + Kéo Chuột Trái`)** hoạt động xuyên suốt kể cả khi đang vẽ dở `Polygon` hoặc `AI-Segment`, kết hợp mở khóa biên **Over-pan 50% Viewport** để đưa tổn thương sát mép ảnh vào chính giữa màn hình.
3. Cung cấp **Phím tắt Lâm sàng (`1`–`7`, `I`)** và **Kéo Chuột Phải chỉnh trực tiếp `WL/WW`** trên Canvas cho ảnh DICOM.

---

## 2. Định danh Tương tác & Hợp đồng Kỹ thuật (Test Hooks & State Contract)

### 2.1. Bảng Định danh Actions, Signals & Cấu hình

| Thành phần | Định danh Kỹ thuật (Hook / Symbol) | Kiểu / Giá trị Chuẩn | Mô tả Hợp đồng |
| :--- | :--- | :--- | :--- |
| **Config Shortcut** | `config["shortcuts"]["pan_mode"]` | `"H"` | Phím tắt mặc định trong [`default_config.yaml`](file:///home/apollai/Documents/GitHub/medical/labelme/labelme/_config/default_config.yaml) để bật chế độ Bàn tay (`Pan`). |
| **Icon File** | `labelme/icons/phosphor/hand.svg` | SVG (`256x256`, `currentColor`) | Icon hiển thị cho nút `Pan` trên Left Toolbar. |
| **Toolbar Action** | `MainWindow._actions.pan_mode` | `QtGui.QAction` (`checkable=True`) | Nằm ngay dưới `_actions.edit_mode` (`Select`) trên thanh công cụ dọc `CreateShapeTools`. |
| **Canvas Mode** | `_CanvasMode.PAN` | Enum member trong `_CanvasMode` | Trạng thái chế độ kéo ảnh bằng chuột trái trên `Canvas`. |
| **Spring-loaded Flag** | `Canvas._is_space_pressed` | `bool` | Cờ ghi nhận phím `Space` đang được nhấn giữ để tạm thời chuyển chuột trái sang hành vi Pan. |
| **Slice Scroll Signal** | `Canvas.slice_scroll_request` | `QtCore.Signal(int)` | Phát giá trị `delta.y()` khi lăn chuột kèm phím `Shift` (lúc `not canvas.is_interacting`). |
| **WL/WW Drag Signal** | `Canvas.window_level_drag_request` | `QtCore.Signal(float, float)` | Phát `(delta_wc, delta_ww)` khi nhấn giữ chuột phải và kéo trên ảnh DICOM. |
| **DICOM Active Flag** | `Canvas._is_dicom_active` | `bool` | Cho biết ảnh đang hiển thị trên Canvas có phiên `_dicom_session` hoạt động hay không. |

### 2.2. Bảng Ánh xạ Phím tắt Nhanh DICOM Presets

| Phím | Mã Preset (`preset_name`) | `Window Center (WL)` | `Window Width (WW)` | Ghi chú Trạng thái |
| :---: | :--- | :---: | :---: | :--- |
| **`1`** | `"auto"` | Theo Header / Percentile `[1, 99]` | Theo Header / Percentile `[1, 99]` | Khôi phục cửa sổ tự động của lát cắt. |
| **`2`** | `"ct_brain"` | `40.0` | `80.0` | Cửa sổ nhu mô não. |
| **`3`** | `"ct_lung"` | `-600.0` | `1500.0` | Cửa sổ nhu mô phổi. |
| **`4`** | `"ct_soft_tissue"` | `40.0` | `400.0` | Cửa sổ mô mềm / trung thất. |
| **`5`** | `"ct_liver"` | `60.0` | `160.0` | Cửa sổ gan. |
| **`6`** | `"ct_bone"` | `400.0` | `1800.0` | Cửa sổ xương. |
| **`7`** | `"ct_stroke"` | `32.0` | `8.0` | Cửa sổ đột quỵ nhồi máu não cấp. |
| **`I`** | *(Giữ nguyên preset)* | *(Giữ nguyên)* | *(Giữ nguyên)* | Đảo trạng thái `_dicom_session.is_inverted`. |

---

## 3. Kịch bản Kiểm thử Hộp xám (Grey-Box Test Cases)

### `TC-ERG-01`: Lăn chuột trực tiếp để Focal Zoom và `Shift + Lăn chuột` để lướt lát cắt
- **Tiền điều kiện**: Khởi tạo `MainWindow` mở một thư mục chứa 3 lát cắt DICOM (`slice_01.dcm`, `slice_02.dcm`, `slice_03.dcm`) kích thước `512x512`.
- **Luồng thực thi & Xác minh Hộp xám**:
  1. Ghi nhận mức zoom ban đầu `z0 = win._canvas_widgets.zoom_widget.value()`.
  2. Gửi sự kiện `QWheelEvent` với `angleDelta = QPoint(0, 120)` và `modifiers = Qt.KeyboardModifier.NoModifier` tại điểm `(480, 480)` gần rìa ảnh.
  3. **Kiểm chứng**: `win._zoom_mode == _ZoomMode.MANUAL_ZOOM` và `win._canvas_widgets.zoom_widget.value() > z0` (phóng to thành công mà không cần giữ `Ctrl`).
  4. Gửi sự kiện `QWheelEvent` với `angleDelta = QPoint(0, -120)` và `modifiers = Qt.KeyboardModifier.ShiftModifier`.
  5. **Kiểm chứng**: `Path(win._image_path).name == "slice_02.dcm"` (chuyển sang lát cắt tiếp theo).
  6. Chuyển sang chế độ vẽ `Polygon`, chấm 2 đỉnh trên `slice_02.dcm` (`canvas.is_drawing == True`), sau đó gửi `Shift + QWheelEvent`.
  7. **Kiểm chứng**: Vẫn giữ nguyên ở `slice_02.dcm` và `len(canvas._current.points) == 2` (chặn chuyển lát cắt khi đang vẽ dở).

### `TC-ERG-02`: Công cụ `Pan (H)` trên Left Toolbar & Kéo vùng rìa ảnh vào giữa màn hình (Over-pan 50% Viewport)
- **Tiền điều kiện**: Mở lát cắt `slice_01.dcm` (`512x512`) trên `MainWindow` có viewport kích thước `800x600`.
- **Luồng thực thi & Xác minh Hộp xám**:
  1. Kiểm tra `win._actions.pan_mode` tồn tại trên thanh công cụ `CreateShapeTools`, có shortcut là `"H"` và đang bật (`isEnabled() == True`).
  2. Kích hoạt `win._actions.pan_mode.trigger()` (hoặc nhấn phím `H`).
  3. **Kiểm chứng**: `canvas.mode == _CanvasMode.PAN`, `win._actions.pan_mode.isChecked() == True`, `win._actions.edit_mode.isChecked() == False`, và con trỏ trên Canvas là `CursorRole.GRAB` (`OpenHandCursor`).
  4. Nhấn giữ chuột trái (`LeftButton`) tại tâm ảnh và kéo một đoạn `(+250, +200)` pixel về phía tâm khung nhìn (dù ảnh chưa tràn viewport hoặc đã chạm biên thanh cuộn).
  5. **Kiểm chứng**: `canvas.get_view_offset().x() > 0` và `canvas.get_view_offset().y() > 0`; tọa độ hiển thị của điểm rìa ảnh `(0, 0)` qua `canvas.transform_image_point_to_widget(point=QPointF(0, 0))` dịch chuyển vào tới tâm khung nhìn mà không bị kẹt ở `0` như giới hạn cũ.

### `TC-ERG-03`: Giữ `Space + Kéo Chuột Trái` (Spring-loaded Hand Pan) khi đang vẽ dở `Polygon` và `AI-Segment`
- **Tiền điều kiện**: Mở ảnh trên `MainWindow`, chọn chế độ vẽ `Polygon` (`create_mode == "polygon"`).
- **Luồng thực thi & Xác minh Hộp xám**:
  1. Click chuột trái chấm 3 đỉnh tạo thành đa giác đang mở (`canvas.is_drawing == True`, `len(canvas._current.points) == 3`).
  2. Nhấn giữ phím `Qt.Key.Key_Space` (`keyPressEvent`).
  3. **Kiểm chứng**:
     - Đa giác **KHÔNG** bị đóng (`canvas.is_drawing == True`, `len(canvas.shapes) == 0`).
     - `canvas._is_space_pressed == True` và `canvas._cursor == CursorRole.GRAB`.
  4. Nhấn giữ chuột trái (`LeftButton`) và kéo từ `(100, 100)` tới `(220, 180)`, sau đó nhả chuột trái.
  5. **Kiểm chứng**:
     - Khung nhìn dịch chuyển (`canvas.get_view_offset()` thay đổi đúng bằng bước kéo).
     - Số đỉnh của đa giác đang vẽ vẫn giữ nguyên là `3` (`len(canvas._current.points) == 3`, không bị chấm thêm đỉnh thứ 4).
  6. Nhả phím `Qt.Key.Key_Space` (`keyReleaseEvent`), click chuột trái tại vị trí mới để chấm đỉnh thứ 4, sau đó nhấn phím `Qt.Key.Key_Return` (`Enter`).
  7. **Kiểm chứng**: Đỉnh thứ 4 được thêm vào và phím `Enter` chốt hoàn tất đa giác (`len(canvas.shapes) == 1`, `len(canvas.shapes[0].points) == 4`).

### `TC-ERG-04`: Phím tắt Nhanh DICOM Presets (`1`–`7` và `I`)
- **Tiền điều kiện**: Mở lát cắt CT ngực `chest_ct_slice.dcm` (có dữ liệu HU thực: phổi `-600 HU`, xương `+750 HU`, mô mềm `+45 HU`).
- **Luồng thực thi & Xác minh Hộp xám**:
  1. Gửi phím `6` (`ct_bone`) vào `MainWindow`.
  2. **Kiểm chứng**: `win._dicom_session.preset_name == "ct_bone"`, `win._dicom_session.window_center == 400.0`, `win._dicom_session.window_width == 1800.0`; giá trị pixel hiển thị trên `canvas.pixmap` tại vùng phổi (`-600 HU`) bằng `0` (đen).
  3. Gửi phím `3` (`ct_lung`) vào `MainWindow`.
  4. **Kiểm chứng**: `win._dicom_session.preset_name == "ct_lung"`, `win._dicom_session.window_center == -600.0`, `win._dicom_session.window_width == 1500.0`; giá trị pixel tại vùng phổi (`-600 HU`) trở về mức xám trung tính (`127` hoặc `128`).
  5. Gửi phím `I` (`Invert Monochrome`) vào `MainWindow`.
  6. **Kiểm chứng**: `win._dicom_session.is_inverted == True`; giá trị pixel tại vùng xương (`+750 HU`) đảo từ `255` sang `0`.
  7. Đặt focus vào ô tìm kiếm file `win._docks.file_search` và gõ phím `"3"`.
  8. **Kiểm chứng**: Chuỗi `"3"` đi vào ô `file_search`, không làm thay đổi trạng thái `is_inverted` hay `preset_name` của `_dicom_session`.

### `TC-ERG-05`: Kéo Chuột Phải chỉnh trực tiếp `WL/WW` trên Canvas & Phân biệt với Click Phải mở Context Menu
- **Tiền điều kiện**: Mở lát cắt `chest_ct_slice.dcm`, đặt cửa sổ ở `ct_soft_tissue` (`WL = 40.0, WW = 400.0`).
- **Luồng thực thi & Xác minh Hộp xám**:
  1. Nhấn giữ nút chuột phải (`RightButton`) tại `(200, 200)`, di chuột tới `(260, 150)` (vượt ngưỡng `startDragDistance`), rồi nhả nút chuột phải.
  2. **Kiểm chứng**:
     - `win._dicom_session.window_width != 400.0` và `win._dicom_session.window_center != 40.0`.
     - `win._dicom_session.preset_name == "custom"`.
     - `canvas.shape_context_menu` và `canvas.canvas_context_menu` **không** bị bật lên khi nhả chuột sau thao tác kéo.
  3. Nhấp chuột phải tại chỗ (nhấn và nhả tại cùng tọa độ `(200, 200)`).
  4. **Kiểm chứng**: Không thay đổi `WL/WW`, và luồng mở Context Menu vẫn được gọi bình thường.

---

## 4. Cổng Kiểm tra Chất lượng (Verification Gate)
- Toàn bộ bài kiểm thử mới (`TC-ERG-01` đến `TC-ERG-05`) trong `tests/unit/test_dicom.py` (hoặc `tests/unit/test_medical_ergonomics.py`) và toàn bộ bộ test hiện hữu của `labelme` (`pytest tests/unit/`) phải **Pass 100%**.
- Kiểm tra tĩnh với `ruff check` và `mypy` / `ty` (nếu có trong môi trường) không phát sinh lỗi.
