from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from labelme import _config
from labelme import _locale
from labelme import _yaml
from labelme._app import MainWindow
from labelme._medical_terminology import CHEST_XRAY_ITEMS
from labelme._medical_terminology import CHEST_XRAY_PRESET
from labelme._medical_terminology import MedicalTerminologyRegistry
from labelme._shape import Shape
from labelme._widgets import LABEL_COLOR_ROLE
from labelme._widgets import LabelDialog
from labelme._widgets import MedicalLabelFormDialog
from labelme._widgets import MedicalPresetFormDialog
from labelme._widgets import UniqueLabelQListWidget


@pytest.fixture()
def isolated_home(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


@pytest.fixture()
def vi_translator(*, qapp: QtWidgets.QApplication) -> Iterator[QtCore.QTranslator]:
    translator = QtCore.QTranslator()
    assert translator.load(str(_locale.TRANSLATE_DIR / "vi_VN.qm"))
    yield translator
    qapp.removeTranslator(translator)


def test_tc_01_default_startup_loads_21_chest_xray_labels_and_colors(
    *,
    qtbot: QtBot,
    isolated_home: Path,
) -> None:
    config_file = isolated_home / ".labelmerc"
    config_file.touch()
    win = MainWindow(config_file=config_file)
    qtbot.addWidget(win)

    unique_list = win._docks.unique_label_list
    expected_labels = [item.canonical_label for item in CHEST_XRAY_ITEMS]
    assert len(expected_labels) == 21
    assert expected_labels[0] == "Lung opacity"
    assert expected_labels[-1] == "Tracheal shift"

    assert unique_list.labels() == expected_labels
    for term_item in CHEST_XRAY_ITEMS:
        list_item = unique_list.find_label_item(label=term_item.canonical_label)
        assert list_item is not None
        assert list_item.data(Qt.ItemDataRole.UserRole) == term_item.canonical_label
        assert list_item.data(LABEL_COLOR_ROLE) == QtGui.QColor(*term_item.color)

    dialog_labels = [
        win._label_dialog.label_list.item(i).data(Qt.ItemDataRole.UserRole)
        for i in range(win._label_dialog.label_list.count())
    ]
    assert dialog_labels == expected_labels
    win.close()


def test_tc_02_locale_aware_display_en_vs_vi_in_all_mode(
    *,
    qtbot: QtBot,
    qapp: QtWidgets.QApplication,
    vi_translator: QtCore.QTranslator,
    isolated_home: Path,
) -> None:
    config_file = isolated_home / ".labelmerc"
    config_file.touch()
    win = MainWindow(config_file=config_file)
    qtbot.addWidget(win)

    unique_list = win._docks.unique_label_list
    dialog = win._label_dialog

    # 1. English (en_US)
    opacity_item = unique_list.find_label_item(label="Lung opacity")
    pleural_calc_item = unique_list.find_label_item(label="Pleural calcification")
    assert opacity_item is not None
    assert pleural_calc_item is not None
    assert opacity_item.text() == "Lung opacity"
    assert pleural_calc_item.text() == "Pleural calcification"
    assert opacity_item.data(Qt.ItemDataRole.UserRole) == "Lung opacity"
    assert pleural_calc_item.data(Qt.ItemDataRole.UserRole) == "Pleural calcification"

    dlg_opacity = dialog._find_item_by_canonical(label="Lung opacity")
    dlg_pleural_calc = dialog._find_item_by_canonical(label="Pleural calcification")
    assert dlg_opacity is not None
    assert dlg_pleural_calc is not None
    assert dlg_opacity.text() == "Lung opacity"
    assert dlg_pleural_calc.text() == "Pleural calcification"

    # 2. Vietnamese (vi_VN via QTranslator)
    qapp.installTranslator(vi_translator)
    QtWidgets.QApplication.processEvents()

    assert opacity_item.text() == "Đám mờ phổi"
    assert pleural_calc_item.text() == "Vôi hóa màng phổi"
    assert opacity_item.data(Qt.ItemDataRole.UserRole) == "Lung opacity"
    assert pleural_calc_item.data(Qt.ItemDataRole.UserRole) == "Pleural calcification"

    assert dlg_opacity.text() == "Đám mờ phổi"
    assert dlg_pleural_calc.text() == "Vôi hóa màng phổi"
    assert dlg_opacity.data(Qt.ItemDataRole.UserRole) == "Lung opacity"
    assert dlg_pleural_calc.data(Qt.ItemDataRole.UserRole) == "Pleural calcification"

    qapp.removeTranslator(vi_translator)
    win.close()


def test_tc_03_context_aware_short_display_by_category(
    *,
    qtbot: QtBot,
    qapp: QtWidgets.QApplication,
    vi_translator: QtCore.QTranslator,
) -> None:
    registry = MedicalTerminologyRegistry()
    dialog = LabelDialog(
        labels=CHEST_XRAY_PRESET.canonical_labels(),
        terminology_registry=registry,
    )
    qtbot.addWidget(dialog)

    unique_list = UniqueLabelQListWidget(
        on_edit_settings_labels=lambda: None,
        on_clear_unused=lambda: None,
        terminology_registry=registry,
    )
    qtbot.addWidget(unique_list)
    for item in CHEST_XRAY_ITEMS:
        unique_list.add_label_item(
            label=item.canonical_label,
            color=item.color,
            from_settings=True,
        )

    # 1. Filter by Lung parenchyma in English
    dialog.category_combo.setCurrentText("Lung parenchyma")
    unique_list.category_combo.setCurrentText("Lung parenchyma")
    visible_dlg_items = dialog.visible_label_items()
    assert len(visible_dlg_items) == 11
    assert len(unique_list.visible_label_items()) == 11

    dlg_opacity = dialog._find_item_by_canonical(label="Lung opacity")
    dlg_nodule = dialog._find_item_by_canonical(label="Pulmonary nodule")
    dlg_mass = dialog._find_item_by_canonical(label="Pulmonary mass")
    assert dlg_opacity is not None and dlg_opacity.text() == "Opacity"
    assert dlg_nodule is not None and dlg_nodule.text() == "Nodule"
    assert dlg_mass is not None and dlg_mass.text() == "Mass"

    # Switch to Vietnamese while still in Lung parenchyma
    qapp.installTranslator(vi_translator)
    assert dlg_opacity.text() == "Đám mờ"
    assert dlg_nodule.text() == "Nốt"
    assert dlg_mass.text() == "Khối"
    ul_opacity = unique_list.find_label_item(label="Lung opacity")
    assert ul_opacity is not None and ul_opacity.text() == "Đám mờ"

    # 2. Filter by Pleura (Màng phổi)
    dialog.category_combo.setCurrentText("Màng phổi")
    unique_list.category_combo.setCurrentText("Màng phổi")
    assert len(dialog.visible_label_items()) == 5
    assert len(unique_list.visible_label_items()) == 5

    dlg_effusion = dialog._find_item_by_canonical(label="Pleural effusion")
    dlg_pleural_calc = dialog._find_item_by_canonical(label="Pleural calcification")
    assert dlg_effusion is not None and dlg_effusion.text() == "Tràn dịch"
    assert dlg_pleural_calc is not None and dlg_pleural_calc.text() == "Vôi hóa"
    assert dlg_pleural_calc.data(Qt.ItemDataRole.UserRole) == "Pleural calcification"

    # Selecting "Vôi hóa" under Pleura must resolve to "Pleural calcification",
    # never "Calcification" of Lung parenchyma.
    dialog._on_label_selected(dlg_pleural_calc)
    dialog._capture_entry()
    assert dialog._entry is not None
    assert dialog._entry.label == "Pleural calcification"

    qapp.removeTranslator(vi_translator)
    assert dlg_effusion.text() == "Effusion"
    assert dlg_pleural_calc.text() == "Calcification"

    # 3. Switch back to All
    dialog.category_combo.setCurrentText("All")
    unique_list.category_combo.setCurrentText("All")
    assert len(dialog.visible_label_items()) == 21
    assert len(unique_list.visible_label_items()) == 21
    assert dlg_opacity.text() == "Lung opacity"
    assert dlg_pleural_calc.text() == "Pleural calcification"


def test_tc_04_vietnamese_short_selection_saves_100_percent_canonical_english_json(
    *,
    qtbot: QtBot,
    qapp: QtWidgets.QApplication,
    vi_translator: QtCore.QTranslator,
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    qapp.installTranslator(vi_translator)
    config_file = isolated_home / ".labelmerc"
    config_file.write_text("auto_save: false\n", encoding="utf-8")

    image_file = tmp_path / "chest_xray_01.png"
    qimg = QtGui.QImage(256, 256, QtGui.QImage.Format.Format_RGB32)
    qimg.fill(QtGui.QColor(0, 0, 0))
    assert qimg.save(str(image_file))

    win = MainWindow(
        config_file=config_file,
        file_or_dir=str(image_file),
        output_dir=str(tmp_path),
    )
    qtbot.addWidget(win)
    win.show()

    dialog = win._label_dialog

    def select_short_vietnamese_label() -> None:
        dialog.category_combo.setCurrentText("Nhu mô phổi")
        opacity_item = dialog._find_item_by_canonical(label="Lung opacity")
        assert opacity_item is not None
        assert opacity_item.text() == "Đám mờ"
        dialog.label_list.itemDoubleClicked.emit(opacity_item)

    QtCore.QTimer.singleShot(0, select_short_vietnamese_label)
    entry = dialog.popup(move=False)
    assert entry is not None
    assert entry.label == "Lung opacity"

    shape = Shape(
        label=entry.label,
        shape_type="rectangle",
        points=np.array([[20.0, 30.0], [120.0, 140.0]], dtype=np.float64),
    )
    win._load_shapes(shapes=[shape], replace=True)

    # RAM shape holds Canonical English
    assert win._canvas_widgets.canvas.shapes[0].label == "Lung opacity"

    # Shape List displays full Vietnamese name "Đám mờ phổi"
    assert len(win._docks.label_list) == 1
    assert win._docks.label_list[0].text() == "Đám mờ phổi"

    # Saved JSON file holds Canonical English "Lung opacity"
    json_path = tmp_path / "test_case.json"
    assert win.save_labels(label_path=str(json_path))
    saved_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert saved_data["shapes"][0]["label"] == "Lung opacity"

    qapp.removeTranslator(vi_translator)
    win.close()


@pytest.mark.parametrize(
    ("query", "expected_canonical"),
    [
        ("collapse", "Atelectasis"),
        ("deviation", "Tracheal shift"),
        ("đông đặc", "Consolidation"),
        ("dong dac", "Consolidation"),
        ("opacity", "Lung opacity"),
    ],
)
def test_tc_05_smart_search_and_aliases_filtering(
    *,
    qtbot: QtBot,
    query: str,
    expected_canonical: str,
) -> None:
    registry = MedicalTerminologyRegistry()
    dialog = LabelDialog(
        labels=CHEST_XRAY_PRESET.canonical_labels(),
        terminology_registry=registry,
    )
    qtbot.addWidget(dialog)

    def type_query_and_accept() -> None:
        dialog.edit.setText(query)
        visible_canonical = dialog.visible_labels()
        assert expected_canonical in visible_canonical
        current = dialog.label_list.currentItem()
        assert current is not None
        assert current.data(Qt.ItemDataRole.UserRole) == expected_canonical
        dialog.accept()

    QtCore.QTimer.singleShot(0, type_query_and_accept)
    entry = dialog.popup(move=False)
    assert entry is not None
    assert entry.label == expected_canonical


def test_tc_06_add_custom_medical_label_via_form_ui_valid_flow(
    *,
    qtbot: QtBot,
    qapp: QtWidgets.QApplication,
    vi_translator: QtCore.QTranslator,
    isolated_home: Path,
) -> None:
    config_file = isolated_home / ".labelmerc"
    config_file.touch()
    win = MainWindow(config_file=config_file)
    qtbot.addWidget(win)

    def fill_and_submit_form() -> None:
        modal = QtWidgets.QApplication.activeModalWidget()
        assert isinstance(modal, MedicalLabelFormDialog)
        modal.english_label_edit.setText("Rib fracture")
        modal.vietnamese_label_edit.setText("Gãy xương sườn")
        modal.short_english_edit.setText("Fracture")
        modal.short_vietnamese_edit.setText("Gãy")
        modal.category_combo.setCurrentText("Chest wall")
        modal.set_color(color=(250, 128, 114))
        modal.ok_button.click()

    QtCore.QTimer.singleShot(0, fill_and_submit_form)
    qtbot.mouseClick(
        win._docks.unique_label_list.add_label_button,
        Qt.MouseButton.LeftButton,
    )

    unique_list = win._docks.unique_label_list
    rib_item = unique_list.find_label_item(label="Rib fracture")
    assert rib_item is not None
    assert rib_item.data(Qt.ItemDataRole.UserRole) == "Rib fracture"
    assert rib_item.data(LABEL_COLOR_ROLE) == QtGui.QColor(250, 128, 114)
    assert win._label_dialog._find_item_by_canonical(label="Rib fracture") is not None

    # Check Vietnamese full and short display
    qapp.installTranslator(vi_translator)
    assert rib_item.text() == "Gãy xương sườn"
    unique_list.category_combo.setCurrentText("Chest wall")
    assert rib_item.text() == "Gãy"
    qapp.removeTranslator(vi_translator)
    unique_list.category_combo.setCurrentText("All")

    # Verify persistence to ~/.labelmerc
    persisted = _yaml.safe_load(stream=config_file.read_text(encoding="utf-8"))
    assert isinstance(persisted, dict)
    assert "custom_terminologies" in persisted
    win.close()

    # Reopen MainWindow and verify custom label survives reload
    reopened = MainWindow(config_file=config_file)
    qtbot.addWidget(reopened)
    assert (
        reopened._docks.unique_label_list.find_label_item(label="Rib fracture")
        is not None
    )
    reopened.close()


def test_tc_07_medical_label_form_dialog_validation_errors(
    *,
    qtbot: QtBot,
) -> None:
    registry = MedicalTerminologyRegistry()
    form = MedicalLabelFormDialog(registry=registry)
    qtbot.addWidget(form)
    form.show()

    # Case A: Blank canonical English label
    form.english_label_edit.setText("   ")
    form.ok_button.click()
    assert form.isVisible()
    assert form.error_label.isVisible()
    assert form.error_label.text() != ""
    assert len(registry.canonical_labels()) == 21

    # Case B: Non-ASCII Vietnamese accented characters in canonical English field
    form.english_label_edit.setText("Gãy xương")
    form.ok_button.click()
    assert form.isVisible()
    assert form.error_label.isVisible()
    assert "ASCII" in form.error_label.text() or "English" in form.error_label.text()
    assert len(registry.canonical_labels()) == 21

    # Case C: Duplicate existing label (case-insensitive)
    form.english_label_edit.setText("lung opacity")
    form.ok_button.click()
    assert form.isVisible()
    assert form.error_label.isVisible()
    assert len(registry.canonical_labels()) == 21

    form.close()


def test_tc_08_preset_switcher_and_create_new_preset_via_form_ui(
    *,
    qtbot: QtBot,
    isolated_home: Path,
) -> None:
    config_file = isolated_home / ".labelmerc"
    config_file.write_text("auto_save: false\n", encoding="utf-8")
    win = MainWindow(config_file=config_file)
    qtbot.addWidget(win)
    unique_list = win._docks.unique_label_list

    assert unique_list.preset_combo.currentData() == "chest_xray"
    assert len(unique_list.settings_labels()) == 21

    # Add an existing shape on canvas before switching presets
    existing_shape = Shape(
        label="Lung opacity",
        shape_type="rectangle",
        points=np.array([[10.0, 10.0], [50.0, 50.0]], dtype=np.float64),
    )
    win._load_shapes(shapes=[existing_shape], replace=True)

    # Create a new preset "Brain CT" via MedicalPresetFormDialog
    preset_dialog = MedicalPresetFormDialog(
        registry=win._terminology_registry,
        on_preset_added=lambda preset: win._on_medical_preset_changed(preset.preset_id),
        parent=win,
    )
    qtbot.addWidget(preset_dialog)
    preset_dialog.preset_name_edit.setText("Brain CT")
    preset_dialog.vietnamese_name_edit.setText("CT Sọ não")
    preset_dialog.accept()

    assert win._terminology_registry.active_preset_id == "brain_ct"
    assert unique_list.preset_combo.currentData() == "brain_ct"

    # Add label "Intracranial hemorrhage" to Brain CT
    label_dialog_form = MedicalLabelFormDialog(
        registry=win._terminology_registry,
        on_label_added=win._on_medical_label_added,
        parent=win,
    )
    qtbot.addWidget(label_dialog_form)
    label_dialog_form.english_label_edit.setText("Intracranial hemorrhage")
    label_dialog_form.vietnamese_label_edit.setText("Xuất huyết nội sọ")
    label_dialog_form.category_combo.setCurrentText("Parenchyma")
    label_dialog_form.accept()

    assert unique_list.settings_labels() == ["Intracranial hemorrhage"]
    # Existing shape on canvas is untouched
    assert len(win._canvas_widgets.canvas.shapes) == 1
    assert win._canvas_widgets.canvas.shapes[0].label == "Lung opacity"

    # Switch back to Chest X-Ray
    unique_list.preset_combo.setCurrentText("Chest X-Ray")
    assert win._terminology_registry.active_preset_id == "chest_xray"
    assert len(unique_list.settings_labels()) == 21
    assert len(win._terminology_registry.categories()) == 4

    # Switch again to Brain CT
    unique_list.preset_combo.setCurrentText("Brain CT")
    assert win._terminology_registry.active_preset_id == "brain_ct"
    assert unique_list.settings_labels() == ["Intracranial hemorrhage"]

    win.close()


def test_tc_09_preselect_short_label_in_right_dock_and_draw_without_popup(
    *,
    qtbot: QtBot,
    qapp: QtWidgets.QApplication,
    vi_translator: QtCore.QTranslator,
    isolated_home: Path,
) -> None:
    qapp.installTranslator(vi_translator)
    config_file = isolated_home / ".labelmerc"
    config_file.write_text(
        "auto_save: false\ndisplay_label_popup: false\n", encoding="utf-8"
    )
    win = MainWindow(config_file=config_file)
    qtbot.addWidget(win)

    unique_list = win._docks.unique_label_list
    unique_list.category_combo.setCurrentText("Màng phổi")
    effusion_item = unique_list.find_label_item(label="Pleural effusion")
    assert effusion_item is not None
    assert effusion_item.text() == "Tràn dịch"
    unique_list.setCurrentItem(effusion_item)
    assert unique_list.selectedItems() == [effusion_item]

    # When drawing a new shape with display_label_popup=False, _ask_new_shape_entry
    # must return the canonical English label "Pleural effusion", not "Tràn dịch"
    entry = win._ask_new_shape_entry(query="")
    assert entry is not None
    assert entry.label == "Pleural effusion"

    qapp.removeTranslator(vi_translator)
    win.close()


@pytest.mark.usefixtures("isolated_home")
def test_tc_10_backward_compatibility_with_explicit_labels_config(
    *,
    qtbot: QtBot,
) -> None:
    config = _config.load_config(
        config_file=None,
        config_overrides={"labels": ["cat", "dog"], "validate_label": "exact"},
    )
    assert config["labels"] == ["cat", "dog"]
    assert config["label_preset"] == "chest_xray"

    win = MainWindow(config_overrides={"labels": ["cat", "dog"]})
    qtbot.addWidget(win)
    assert win._docks.unique_label_list.labels() == ["cat", "dog"]
    win.close()
