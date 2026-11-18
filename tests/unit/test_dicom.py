from __future__ import annotations

import json
from collections.abc import Callable
from collections.abc import Generator
from pathlib import Path

import numpy as np
import PIL.Image
import pytest
from pydicom.dataset import FileDataset
from pydicom.dataset import FileMetaDataset
from pydicom.uid import UID
from pydicom.uid import ExplicitVRLittleEndian
from pydicom.uid import generate_uid
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6.QtCore import QPoint
from PySide6.QtCore import QPointF
from PySide6.QtCore import QSettings
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from labelme import _app
from labelme import _dicom
from labelme._app import MainWindow
from labelme._app import _ZoomMode
from labelme._label_file import ImageDecodeLimitError
from labelme._label_file import read_image_file
from labelme._shape import Shape
from labelme._utils._image import img_qt_to_arr
from labelme._widgets import LabelDialogEntry
from labelme._widgets._canvas import _CanvasMode
from labelme._widgets._canvas_interaction import CursorRole


@pytest.fixture(autouse=True)
def _isolated_qtsettings(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    settings_file = tmp_path / "qtsettings.ini"
    settings = QSettings(str(settings_file), QSettings.Format.IniFormat)
    monkeypatch.setattr(_app.QtCore, "QSettings", lambda *_args, **_kwargs: settings)
    yield


def _create_chest_ct_dicom(
    *,
    path: Path,
    rows: int = 128,
    cols: int = 128,
    instance_number: int = 1,
) -> Path:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = UID("1.2.840.10008.5.1.4.1.1.2")
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\x00" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.FrameOfReferenceUID = generate_uid()
    ds.InstanceNumber = instance_number

    # Realistic clinical PII tags that MUST be stripped by the Strict Allowlist
    ds.PatientName = "NGUYEN^VAN^AN"
    ds.PatientID = "BN-2026-9981"
    ds.PatientBirthDate = "19750412"
    ds.PatientSex = "M"
    ds.InstitutionName = "Benh Vien Cho Ray"
    ds.ReferringPhysicianName = "BS^TRAN^MINH"

    ds.Modality = "CT"
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = rows
    ds.Columns = cols
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1

    ds.RescaleSlope = 1.0
    ds.RescaleIntercept = -1024.0
    ds.RescaleType = "HU"
    ds.WindowCenter = -600.0
    ds.WindowWidth = 1500.0

    ds.PixelSpacing = [0.703125, 0.703125]
    ds.SliceThickness = 1.25
    ds.SpacingBetweenSlices = 1.25
    ds.ImagePositionPatient = [-180.0, -180.0, -45.5]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    # Stored raw values: HU = raw * 1.0 - 1024.0 => raw = HU + 1024
    # Default lung parenchyma: -600 HU -> raw 424
    raw = np.full((rows, cols), 424, dtype=np.int16)
    if rows >= 100 and cols >= 100:
        # Trachea air: -950 HU -> raw 74
        raw[10:20, 10:20] = 74
        # Mediastinum soft tissue: +45 HU -> raw 1069
        raw[30:50, 30:50] = 1069
        # Thoracic vertebra bone: +750 HU -> raw 1774
        raw[80:100, 80:100] = 1774

    ds.PixelData = raw.tobytes()
    ds.save_as(str(path), enforce_file_format=True)
    return path


def _create_chest_dx_dicom(*, path: Path, photometric: str) -> Path:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = UID("1.2.840.10008.5.1.4.1.1.1.1")
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\x00" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = "DX"
    ds.PhotometricInterpretation = photometric
    ds.Rows = 32
    ds.Columns = 32
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 16
    ds.BitsStored = 12
    ds.HighBit = 11
    ds.PixelRepresentation = 0
    ds.WindowCenter = 2000.0
    ds.WindowWidth = 4000.0

    raw = np.zeros((32, 32), dtype=np.uint16)
    raw[:, :16] = 0
    raw[:, 16:] = 4000
    ds.PixelData = raw.tobytes()
    ds.save_as(str(path), enforce_file_format=True)
    return path


def _make_window(*, qtbot: QtBot, file_or_dir: str) -> MainWindow:
    win = MainWindow(
        config_overrides={"auto_save": False, "show_label_text_field": True},
        file_or_dir=file_or_dir,
    )
    qtbot.addWidget(win)
    return win


def test_tc_dcm_01_supported_extensions_and_directory_scan(*, tmp_path: Path) -> None:
    extensions = _app._list_supported_image_extensions()
    assert ".dcm" in extensions
    assert ".dicom" in extensions
    assert _dicom.is_dicom_file(filename="slice_01.DCM")
    assert _dicom.is_dicom_file(filename=Path("series/slice_02.dicom"))
    assert not _dicom.is_dicom_file(filename="photo.png")

    _create_chest_ct_dicom(path=tmp_path / "slice_2.dcm")
    _create_chest_ct_dicom(path=tmp_path / "slice_10.dicom")
    PIL.Image.new("RGB", (16, 16)).save(tmp_path / "slice_1.png")
    (tmp_path / "slice_2.json").write_text("{}", encoding="utf-8")

    scanned = [Path(p).name for p in _app._scan_image_files(root_dir=str(tmp_path))]
    assert scanned == ["slice_1.png", "slice_2.dcm", "slice_10.dicom"]


def test_tc_dcm_02_modality_lut_hounsfield_units_and_windowing(
    *, tmp_path: Path
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    session = _dicom.load_dicom_session(filename=dcm_path)

    assert session.hu_array.dtype == np.float32
    assert session.hu_array.shape == (128, 128)
    assert session.hu_array[15, 15] == -950.0
    assert session.hu_array[64, 64] == -600.0
    assert session.hu_array[40, 40] == 45.0
    assert session.hu_array[90, 90] == 750.0

    lung_u8 = _dicom.apply_dicom_window(
        hu_array=session.hu_array,
        window_center=-600.0,
        window_width=1500.0,
        invert=False,
    )
    assert lung_u8.dtype == np.uint8
    assert lung_u8[64, 64] in (127, 128)
    assert lung_u8[90, 90] == 255


def test_tc_dcm_03_monochrome1_vs_monochrome2_inversion(*, tmp_path: Path) -> None:
    mono1_path = _create_chest_dx_dicom(
        path=tmp_path / "chest_dx_mono1.dcm", photometric="MONOCHROME1"
    )
    mono2_path = _create_chest_dx_dicom(
        path=tmp_path / "chest_dx_mono2.dcm", photometric="MONOCHROME2"
    )

    session_mono2 = _dicom.load_dicom_session(filename=mono2_path)
    assert session_mono2.is_inverted is False
    rendered_mono2 = session_mono2.render_uint8()
    assert rendered_mono2[0, 0] == 0
    assert rendered_mono2[0, 24] == 255

    session_mono1 = _dicom.load_dicom_session(filename=mono1_path)
    assert session_mono1.is_inverted is True
    rendered_mono1 = session_mono1.render_uint8()
    assert rendered_mono1[0, 0] == 255
    assert rendered_mono1[0, 24] == 0


def test_tc_dcm_04_strict_pii_sanitization_and_3d_geometry_in_json(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))

    shape = Shape(
        label="lung_nodule",
        shape_type="polygon",
        points=np.array([[20.0, 20.0], [40.0, 20.0], [30.0, 40.0]], dtype=np.float64),
        closed=True,
    )
    win._load_shapes(shapes=[shape], replace=True)

    json_path = tmp_path / "chest_ct_slice.json"
    assert win.save_labels(label_path=str(json_path))
    win._wait_for_save()
    assert json_path.is_file()

    raw_text = json_path.read_text(encoding="utf-8")
    for forbidden_pii in (
        "NGUYEN",
        "BN-2026-9981",
        "19750412",
        "Cho Ray",
        "TRAN",
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "InstitutionName",
    ):
        assert forbidden_pii not in raw_text

    payload = json.loads(raw_text)
    assert payload["imageData"] is None
    geometry = payload["dicom"]["geometry"]
    assert geometry["pixelSpacingMm"] == [0.703125, 0.703125]
    assert geometry["sliceThicknessMm"] == 1.25
    assert geometry["imagePositionPatient"] == [-180.0, -180.0, -45.5]
    assert geometry["imageOrientationPatient"] == [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    win.close()


def test_tc_dcm_05_interactive_ww_wl_presets_preserve_16bit_dynamic_range(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))
    canvas = win._canvas_widgets.canvas

    dialog = win.create_brightness_contrast_dialog()
    qtbot.addWidget(dialog)

    dialog.combo_preset.setCurrentText("ct_bone")
    assert dialog.window_center == 400.0
    assert dialog.window_width == 1800.0
    bone_key = canvas.pixmap.cacheKey()
    bone_arr = img_qt_to_arr(img_qt=canvas.pixmap.toImage())
    # In bone window (WL=400, WW=1800 -> [-500, 1300]), lung (-600 HU) is clipped to 0
    assert bone_arr[64, 64, 0] == 0
    # Bone (+750 HU) is mid-gray (not saturated to 255)
    assert 150 < bone_arr[90, 90, 0] < 200

    # Switch back to lung preset: must recover full 16-bit/float lung detail
    dialog.combo_preset.setCurrentText("ct_lung")
    assert dialog.window_center == -600.0
    assert dialog.window_width == 1500.0
    lung_key = canvas.pixmap.cacheKey()
    assert lung_key != bone_key
    lung_arr = img_qt_to_arr(img_qt=canvas.pixmap.toImage())
    assert lung_arr[64, 64, 0] in (127, 128)
    assert lung_arr[90, 90, 0] == 255

    dialog.check_invert.setChecked(True)
    inv_key = canvas.pixmap.cacheKey()
    assert inv_key != lung_key
    inv_arr = img_qt_to_arr(img_qt=canvas.pixmap.toImage())
    assert inv_arr[90, 90, 0] == 0
    win.close()


def test_tc_dcm_06_zero_loss_save_and_restore_view_state(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))

    dialog = win.create_brightness_contrast_dialog()
    qtbot.addWidget(dialog)
    dialog.combo_preset.setCurrentText("ct_soft_tissue")
    assert win._dicom_session is not None
    assert win._dicom_session.window_center == 40.0
    assert win._dicom_session.window_width == 400.0

    json_path = tmp_path / "chest_ct_slice.json"
    assert win.save_labels(label_path=str(json_path))
    win._wait_for_save()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["imageData"] is None
    assert payload["dicom"]["viewState"] == {
        "appliedWindowCenter": 40.0,
        "appliedWindowWidth": 400.0,
        "appliedPresetName": "ct_soft_tissue",
        "isInverted": False,
    }
    win.close()

    win_reloaded = _make_window(qtbot=qtbot, file_or_dir=str(json_path))
    assert win_reloaded._dicom_session is not None
    assert win_reloaded._dicom_session.window_center == 40.0
    assert win_reloaded._dicom_session.window_width == 400.0
    assert win_reloaded._dicom_session.preset_name == "ct_soft_tissue"
    assert win_reloaded._dicom_session.hu_array[64, 64] == -600.0
    win_reloaded.close()


def test_tc_dcm_07_slicer_data_probe_on_status_bar(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    jpg_path = tmp_path / "normal.jpg"
    PIL.Image.new("RGB", (128, 128), color=(100, 120, 140)).save(jpg_path)

    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))
    canvas = win._canvas_widgets.canvas

    canvas.mouse_moved.emit(QPointF(64.0, 64.0))
    assert "HU: -600" in win._status_bar.stats.text()

    canvas.mouse_moved.emit(QPointF(90.0, 90.0))
    assert "HU: 750" in win._status_bar.stats.text()

    assert win._load_file(image_or_label_path=str(jpg_path))
    assert "HU:" not in win._status_bar.stats.text()
    canvas.mouse_moved.emit(QPointF(50.0, 60.0))
    assert win._status_bar.stats.text() == "x   50   y   60"
    win.close()


def test_tc_dcm_08_check_decodable_memory_limit_on_large_dicom(
    *,
    tmp_path: Path,
    set_allocation_limit: Callable[[int], None],
) -> None:
    set_allocation_limit(1)
    large_dcm = _create_chest_ct_dicom(
        path=tmp_path / "large_ct.dcm", rows=1024, cols=1024
    )
    with pytest.raises(ImageDecodeLimitError) as exc_info:
        read_image_file(filename=str(large_dcm), max_decode_mb=1)
    assert exc_info.value.width == 1024
    assert exc_info.value.height == 1024
    assert exc_info.value.required_mb == 4


def test_tc_dcm_09_real_patient001_dicom_file(*, qtbot: QtBot) -> None:
    real_dcm = Path(
        "/home/apollai/Documents/GitHub/medical/image-annotator/images/Patient001/instance-0001.dcm"
    )
    if not real_dcm.is_file():
        pytest.skip("Sample Patient001 DICOM file not present")

    image_bytes = read_image_file(filename=str(real_dcm))
    assert image_bytes[:4] == b"\x89PNG"

    win = _make_window(qtbot=qtbot, file_or_dir=str(real_dcm))
    assert not win._image.isNull()
    assert win._image.width() == 512
    assert win._image.height() == 512
    assert win._dicom_session is not None
    assert win._dicom_session.modality == "CT"
    assert not win._canvas_widgets.canvas.pixmap.isNull()
    win.close()


def test_tc_dcm_10_keep_prev_window_level_across_dicom_series(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    _create_chest_ct_dicom(path=tmp_path / "slice_01.dcm", instance_number=1)
    _create_chest_ct_dicom(path=tmp_path / "slice_02.dcm", instance_number=2)

    win = _make_window(qtbot=qtbot, file_or_dir=str(tmp_path))
    win._actions.toggle_keep_prev_brightness_contrast.trigger()
    assert win._actions.toggle_keep_prev_brightness_contrast.isChecked()

    dialog = win.create_brightness_contrast_dialog()
    qtbot.addWidget(dialog)
    dialog.combo_preset.setCurrentText("ct_bone")
    assert win._dicom_session is not None
    assert win._dicom_session.window_center == 400.0
    assert win._dicom_session.window_width == 1800.0

    win._actions.open_next_img.trigger()
    assert win._image_path is not None
    assert Path(win._image_path).name == "slice_02.dcm"
    assert win._dicom_session is not None
    assert win._dicom_session.window_center == 400.0
    assert win._dicom_session.window_width == 1800.0
    assert win._dicom_session.preset_name == "ct_bone"
    win.close()


def _make_wheel_event(
    *,
    pos: QPointF,
    angle_delta: QPoint,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> QtGui.QWheelEvent:
    return QtGui.QWheelEvent(
        pos,
        pos,
        QPoint(0, 0),
        angle_delta,
        Qt.MouseButton.NoButton,
        modifiers,
        Qt.ScrollPhase.NoScrollPhase,
        False,  # noqa: FBT003 -- QWheelEvent takes inverted positionally
    )


def test_tc_erg_01_direct_wheel_focal_zoom_and_shift_wheel_slice_scroll(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    for idx in (1, 2, 3):
        _create_chest_ct_dicom(
            path=tmp_path / f"slice_0{idx}.dcm",
            rows=512,
            cols=512,
            instance_number=idx,
        )

    win = _make_window(qtbot=qtbot, file_or_dir=str(tmp_path))
    canvas = win._canvas_widgets.canvas
    z0 = win._canvas_widgets.zoom_widget.value()

    canvas.wheelEvent(
        _make_wheel_event(
            pos=QPointF(480.0, 480.0),
            angle_delta=QPoint(0, 120),
            modifiers=Qt.KeyboardModifier.NoModifier,
        )
    )
    assert win._zoom_mode == _ZoomMode.MANUAL_ZOOM
    assert win._canvas_widgets.zoom_widget.value() > z0

    canvas.wheelEvent(
        _make_wheel_event(
            pos=QPointF(256.0, 256.0),
            angle_delta=QPoint(0, -120),
            modifiers=Qt.KeyboardModifier.ShiftModifier,
        )
    )
    assert win._image_path is not None
    assert Path(win._image_path).name == "slice_02.dcm"

    win._switch_canvas_mode(edit=False, create_mode="polygon")
    p1 = canvas.transform_image_point_to_widget(point=QPointF(100.0, 100.0)).toPoint()
    p2 = canvas.transform_image_point_to_widget(point=QPointF(200.0, 100.0)).toPoint()
    qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=p1)
    qtbot.mouseMove(canvas, pos=p2)
    qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=p2)
    assert canvas.is_drawing is True
    assert canvas._current is not None
    assert len(canvas._current.points) == 2

    canvas.wheelEvent(
        _make_wheel_event(
            pos=QPointF(256.0, 256.0),
            angle_delta=QPoint(0, -120),
            modifiers=Qt.KeyboardModifier.ShiftModifier,
        )
    )
    assert win._image_path is not None
    assert Path(win._image_path).name == "slice_02.dcm"
    assert canvas._current is not None
    assert len(canvas._current.points) == 2
    canvas._release_cursor()
    win.close()


def test_tc_erg_02_pan_tool_and_overpan_50_percent_viewport(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    dcm_path = _create_chest_ct_dicom(
        path=tmp_path / "slice_01.dcm", rows=512, cols=512
    )
    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))
    win.resize(1100, 750)
    win._set_zoom_to_original()
    canvas = win._canvas_widgets.canvas
    viewport = win._canvas_widgets.scroll_area.viewport()
    viewport.resize(800, 600)

    assert win._actions.pan_mode.isEnabled() is True
    assert win._actions.pan_mode.shortcut().toString() == "H"

    win._actions.pan_mode.trigger()
    assert canvas.mode == _CanvasMode.PAN
    assert win._actions.pan_mode.isChecked() is True
    assert win._actions.edit_mode.isChecked() is False
    assert canvas._cursor == CursorRole.GRAB

    edge_before = canvas.transform_image_point_to_widget(point=QPointF(0.0, 0.0))
    start = QPoint(256, 256)
    end = QPoint(256 + 250, 256 + 200)
    qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=start)
    assert canvas._cursor == CursorRole.MOVE
    canvas.mouseMoveEvent(
        QtGui.QMouseEvent(
            QtCore.QEvent.Type.MouseMove,
            QPointF(end),
            QPointF(canvas.mapToGlobal(end)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=end)

    assert canvas.get_view_offset().x() > 0
    assert canvas.get_view_offset().y() > 0
    edge_after = canvas.transform_image_point_to_widget(point=QPointF(0.0, 0.0))
    assert edge_after.x() > edge_before.x()
    assert edge_after.y() > edge_before.y()
    canvas._release_cursor()
    win.close()


def test_tc_erg_03_spring_loaded_space_pan_while_drawing_polygon(
    *, tmp_path: Path, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    dcm_path = _create_chest_ct_dicom(
        path=tmp_path / "slice_01.dcm", rows=512, cols=512
    )
    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))
    monkeypatch.setattr(
        win._label_dialog,
        "popup",
        lambda **_kwargs: LabelDialogEntry(
            label="lung_lesion", flags={}, group_id=None, description=""
        ),
    )
    win._set_zoom_to_original()
    canvas = win._canvas_widgets.canvas

    win._switch_canvas_mode(edit=False, create_mode="polygon")
    for pt in (QPointF(50.0, 50.0), QPointF(150.0, 50.0), QPointF(150.0, 150.0)):
        wpt = canvas.transform_image_point_to_widget(point=pt).toPoint()
        qtbot.mouseMove(canvas, pos=wpt)
        qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=wpt)

    assert canvas.is_drawing is True
    assert canvas._current is not None
    assert len(canvas._current.points) == 3

    qtbot.keyPress(canvas, Qt.Key.Key_Space)
    assert canvas.is_drawing is True
    assert len(canvas.shapes) == 0
    assert canvas._is_space_pressed is True
    assert canvas._cursor == CursorRole.GRAB

    offset_before = canvas.get_view_offset()
    drag_start = QPoint(100, 100)
    drag_end = QPoint(220, 180)
    qtbot.mousePress(canvas, Qt.MouseButton.LeftButton, pos=drag_start)
    canvas.mouseMoveEvent(
        QtGui.QMouseEvent(
            QtCore.QEvent.Type.MouseMove,
            QPointF(drag_end),
            QPointF(canvas.mapToGlobal(drag_end)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    qtbot.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=drag_end)

    assert canvas.get_view_offset() != offset_before
    assert canvas._current is not None
    assert len(canvas._current.points) == 3

    qtbot.keyRelease(canvas, Qt.Key.Key_Space)
    assert canvas._is_space_pressed is False

    pt4 = canvas.transform_image_point_to_widget(point=QPointF(50.0, 150.0)).toPoint()
    qtbot.mouseMove(canvas, pos=pt4)
    qtbot.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=pt4)
    assert canvas._current is not None
    assert len(canvas._current.points) == 4

    qtbot.keyClick(canvas, Qt.Key.Key_Return)
    assert len(canvas.shapes) == 1
    assert len(canvas.shapes[0].points) == 4
    canvas._release_cursor()
    win.mark_clean()
    win.close()


def test_tc_erg_04_dicom_preset_shortcuts_1_to_7_and_invert(
    *, tmp_path: Path, qtbot: QtBot
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))
    canvas = win._canvas_widgets.canvas
    assert win._dicom_session is not None

    qtbot.keyClick(win, Qt.Key.Key_6)
    assert win._dicom_session.preset_name == "ct_bone"
    assert win._dicom_session.window_center == 400.0
    assert win._dicom_session.window_width == 1800.0
    bone_arr = img_qt_to_arr(img_qt=canvas.pixmap.toImage())
    assert bone_arr[64, 64, 0] == 0

    qtbot.keyClick(win, Qt.Key.Key_3)
    assert win._dicom_session.preset_name == "ct_lung"
    assert win._dicom_session.window_center == -600.0
    assert win._dicom_session.window_width == 1500.0
    lung_arr = img_qt_to_arr(img_qt=canvas.pixmap.toImage())
    assert lung_arr[64, 64, 0] in (127, 128)
    assert lung_arr[90, 90, 0] == 255

    qtbot.keyClick(win, Qt.Key.Key_I)
    assert win._dicom_session.is_inverted is True
    inv_arr = img_qt_to_arr(img_qt=canvas.pixmap.toImage())
    assert inv_arr[90, 90, 0] == 0

    win._docks.file_search.setFocus()
    qtbot.keyClicks(win._docks.file_search, "3")
    assert win._docks.file_search.text() == "3"
    assert win._dicom_session.is_inverted is True
    assert win._dicom_session.preset_name == "ct_lung"
    win.close()


def test_tc_erg_05_right_drag_adjusts_wl_ww_without_opening_context_menu(
    *, tmp_path: Path, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))
    canvas = win._canvas_widgets.canvas
    assert win._dicom_session is not None

    qtbot.keyClick(win, Qt.Key.Key_4)
    assert win._dicom_session.preset_name == "ct_soft_tissue"
    assert win._dicom_session.window_center == 40.0
    assert win._dicom_session.window_width == 400.0

    opened_menus: list[str] = []
    monkeypatch.setattr(
        canvas.shape_context_menu,
        "exec",
        lambda *_args, **_kwargs: opened_menus.append("shape"),
    )
    monkeypatch.setattr(
        canvas.canvas_context_menu,
        "exec",
        lambda *_args, **_kwargs: opened_menus.append("canvas"),
    )

    start = QPoint(200, 200)
    end = QPoint(260, 150)
    qtbot.mousePress(canvas, Qt.MouseButton.RightButton, pos=start)
    canvas.mouseMoveEvent(
        QtGui.QMouseEvent(
            QtCore.QEvent.Type.MouseMove,
            QPointF(end),
            QPointF(canvas.mapToGlobal(end)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    qtbot.mouseRelease(canvas, Qt.MouseButton.RightButton, pos=end)

    assert win._dicom_session.window_width != 400.0
    assert win._dicom_session.window_center != 40.0
    assert win._dicom_session.preset_name == "custom"
    assert opened_menus == []

    wc_after_drag = win._dicom_session.window_center
    ww_after_drag = win._dicom_session.window_width
    qtbot.mousePress(canvas, Qt.MouseButton.RightButton, pos=start)
    qtbot.mouseRelease(canvas, Qt.MouseButton.RightButton, pos=start)
    assert win._dicom_session.window_center == wc_after_drag
    assert win._dicom_session.window_width == ww_after_drag
    assert opened_menus == ["canvas"]
    win.close()


def test_about_dialog_includes_medical_dicom_support(
    *, tmp_path: Path, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    dcm_path = _create_chest_ct_dicom(path=tmp_path / "chest_ct_slice.dcm")
    captured_about: list[tuple[str, str]] = []
    monkeypatch.setattr(
        _app.QMessageBox,
        "about",
        lambda _parent, title, text: captured_about.append((title, text)),
    )

    win = _make_window(qtbot=qtbot, file_or_dir=str(dcm_path))
    win._actions.about.trigger()

    assert len(captured_about) == 1
    _title, html_text = captured_about[0]
    assert "Medical DICOM" in html_text
    assert ".dcm" in html_text
    assert ".dicom" in html_text
    assert "Hounsfield Unit" in html_text
    assert "WL/WW" in html_text
    win.close()


def test_build_installers_workflow_release_job_has_repo_context() -> None:
    workflow_path = (
        Path(__file__).resolve().parents[2]
        / ".github"
        / "workflows"
        / "build-installers.yml"
    )
    content = workflow_path.read_text(encoding="utf-8")
    release_section = content.split("  release:", maxsplit=1)[1]

    assert "actions/checkout@" in release_section
    assert "GH_REPO: ${{ github.repository }}" in release_section
    assert 'gh release view "${GITHUB_REF_NAME}" --repo "${GITHUB_REPOSITORY}"' in (
        release_section
    )
    assert 'gh release upload "${GITHUB_REF_NAME}" release-assets/* --repo' in (
        release_section
    )
    assert '--repo "${GITHUB_REPOSITORY}"' in release_section
