from __future__ import annotations

from collections.abc import Callable
from typing import Final
from typing import override

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from .._medical_terminology import MedicalTerminologyRegistry
from .._medical_terminology import TerminologyItem
from .._medical_terminology import TerminologyPreset
from .._medical_terminology import get_terminology_registry
from .._medical_terminology import strip_accents

NEW_PRESET_SENTINEL: Final[str] = "__new_preset__"


class CategoryFilterComboBox(QtWidgets.QComboBox):
    _registry: MedicalTerminologyRegistry

    def __init__(
        self,
        *,
        registry: MedicalTerminologyRegistry | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("category_combo")
        self.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.setMinimumContentsLength(6)
        self.setMinimumWidth(60)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self._registry = (
            registry if registry is not None else get_terminology_registry()
        )
        self.refresh_categories()

    def set_registry(self, *, registry: MedicalTerminologyRegistry) -> None:
        self._registry = registry
        self.refresh_categories()

    def active_category_id(self) -> str | None:
        data = self.currentData()
        if not isinstance(data, str) or data == "all":
            return None
        return data

    def _update_popup_minimum_width(self) -> None:
        view = self.view()
        if view is None:
            return
        POPUP_PADDING: Final[int] = 28
        col_hint = view.sizeHintForColumn(0)
        if col_hint > 0:
            view.setMinimumWidth(max(self.width(), col_hint + POPUP_PADDING))

    @override
    def showPopup(self) -> None:
        self._update_popup_minimum_width()
        super().showPopup()

    def refresh_categories(self, *, keep_category_id: str | None = None) -> None:
        current = (
            keep_category_id if keep_category_id is not None else self.currentData()
        )
        locale = self._registry.get_locale()
        with QtCore.QSignalBlocker(self):
            self.clear()
            self.addItem(self.tr("All"), "all")
            for cat in self._registry.categories():
                self.addItem(cat.display_name(locale=locale), cat.category_id)
            idx = self.findData(current) if current else 0
            self.setCurrentIndex(idx if idx >= 0 else 0)
        self._update_popup_minimum_width()

    def resolve_index(self, *, text_or_id: str) -> int:
        cleaned = text_or_id.strip()
        if not cleaned or cleaned.lower() in (
            "all",
            "tất cả",
            "tat ca",
            "all categories",
            "tất cả nhóm",
        ):
            return 0
        for i in range(self.count()):
            if (
                self.itemText(i).lower() == cleaned.lower()
                or str(self.itemData(i) or "").lower() == cleaned.lower()
            ):
                return i
        resolved_cat = self._registry.resolve_category_id(category_id_or_name=cleaned)
        if resolved_cat is not None:
            idx = self.findData(resolved_cat)
            if idx >= 0:
                return idx
        cleaned_ascii = strip_accents(text=cleaned.lower())
        for i in range(self.count()):
            item_ascii = strip_accents(text=self.itemText(i).lower())
            if cleaned_ascii in item_ascii:
                return i
        return -1

    @override
    def setCurrentText(self, text: str, /) -> None:
        idx = self.resolve_index(text_or_id=text)
        if idx >= 0:
            self.setCurrentIndex(idx)
        else:
            super().setCurrentText(text)


class PresetSelectorComboBox(QtWidgets.QComboBox):
    _registry: MedicalTerminologyRegistry

    def __init__(
        self,
        *,
        registry: MedicalTerminologyRegistry | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("preset_combo")
        self._registry = (
            registry if registry is not None else get_terminology_registry()
        )
        self.refresh_presets()

    def set_registry(self, *, registry: MedicalTerminologyRegistry) -> None:
        self._registry = registry
        self.refresh_presets()

    def refresh_presets(self) -> None:
        locale = self._registry.get_locale()
        active_id = self._registry.active_preset_id
        with QtCore.QSignalBlocker(self):
            self.clear()
            for preset in self._registry.presets():
                self.addItem(preset.display_name(locale=locale), preset.preset_id)
            self.addItem(self.tr("+ New Preset…"), NEW_PRESET_SENTINEL)
            idx = self.findData(active_id)
            self.setCurrentIndex(idx if idx >= 0 else 0)

    def resolve_index(self, *, text_or_id: str) -> int:
        cleaned = text_or_id.strip().lower()
        for i in range(self.count()):
            data = str(self.itemData(i) or "").lower()
            text = self.itemText(i).lower()
            if cleaned in (data, text):
                return i
        for preset in self._registry.presets():
            if cleaned not in (
                preset.preset_id.lower(),
                preset.en_name.lower(),
                preset.vi_name.lower(),
                strip_accents(text=preset.vi_name.lower()),
            ):
                continue
            idx = self.findData(preset.preset_id)
            if idx >= 0:
                return idx
        for i in range(self.count()):
            if cleaned in self.itemText(i).lower():
                return i
        return -1

    @override
    def setCurrentText(self, text: str, /) -> None:
        idx = self.resolve_index(text_or_id=text)
        if idx >= 0:
            self.setCurrentIndex(idx)
        else:
            super().setCurrentText(text)


class MedicalLabelFormDialog(QtWidgets.QDialog):
    """Form UI for adding a new medical terminology label with validation."""

    _registry: MedicalTerminologyRegistry
    _on_label_added: Callable[[TerminologyItem], None] | None
    _selected_color: tuple[int, int, int]

    english_label_edit: QtWidgets.QLineEdit
    vietnamese_label_edit: QtWidgets.QLineEdit
    short_english_edit: QtWidgets.QLineEdit
    short_vietnamese_edit: QtWidgets.QLineEdit
    category_combo: QtWidgets.QComboBox
    color_button: QtWidgets.QPushButton
    error_label: QtWidgets.QLabel
    ok_button: QtWidgets.QPushButton
    cancel_button: QtWidgets.QPushButton
    created_item: TerminologyItem | None

    def __init__(
        self,
        *,
        registry: MedicalTerminologyRegistry | None = None,
        on_label_added: Callable[[TerminologyItem], None] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._registry = (
            registry if registry is not None else get_terminology_registry()
        )
        self._on_label_added = on_label_added
        self.created_item = None

        title = self.tr("Add Medical Label")
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        self.setMinimumWidth(380)

        self.english_label_edit = QtWidgets.QLineEdit()
        self.english_label_edit.setObjectName("english_label_edit")
        self.english_label_edit.setPlaceholderText(
            self.tr("e.g. Rib fracture (Canonical English for AI JSON)")
        )

        self.vietnamese_label_edit = QtWidgets.QLineEdit()
        self.vietnamese_label_edit.setObjectName("vietnamese_label_edit")
        self.vietnamese_label_edit.setPlaceholderText(
            self.tr("Display name in local language (Optional)")
        )

        self.short_english_edit = QtWidgets.QLineEdit()
        self.short_english_edit.setObjectName("short_english_edit")
        self.short_english_edit.setPlaceholderText(
            self.tr("e.g. Fracture (Short name in category)")
        )

        self.short_vietnamese_edit = QtWidgets.QLineEdit()
        self.short_vietnamese_edit.setObjectName("short_vietnamese_edit")
        self.short_vietnamese_edit.setPlaceholderText(
            self.tr("Short localized name in category (Optional)")
        )

        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.setObjectName("category_combo")
        self.category_combo.setEditable(True)
        for cat in self._registry.categories():
            self.category_combo.addItem(cat.en_name, cat.category_id)

        self._selected_color = self._registry.suggest_next_color()
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setObjectName("color_button")
        self.color_button.clicked.connect(self._choose_color)
        self._update_color_button_style()

        self.error_label = QtWidgets.QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #d93025; font-weight: 500;")
        self.error_label.hide()

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(
            self.tr("Canonical English Label *:"), self.english_label_edit
        )
        form_layout.addRow(
            self.tr("Localized Display Name:"), self.vietnamese_label_edit
        )
        form_layout.addRow(self.tr("Short English Name:"), self.short_english_edit)
        form_layout.addRow(
            self.tr("Short Localized Name:"), self.short_vietnamese_edit
        )
        form_layout.addRow(self.tr("Anatomical Category:"), self.category_combo)
        form_layout.addRow(self.tr("Display Color:"), self.color_button)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = button_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.error_label)
        main_layout.addWidget(button_box)

    @property
    def selected_color(self) -> tuple[int, int, int]:
        return self._selected_color

    def set_color(self, *, color: tuple[int, int, int]) -> None:
        self._selected_color = color
        self._update_color_button_style()

    def _update_color_button_style(self) -> None:
        r, g, b = self._selected_color
        self.color_button.setText(f"RGB({r}, {g}, {b})")
        self.color_button.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); "
            "color: #000000; padding: 4px 8px; border: 1px solid #888888;"
        )

    def _choose_color(self) -> None:
        initial = QtGui.QColor(*self._selected_color)
        chosen = QtWidgets.QColorDialog.getColor(initial, self)
        if chosen.isValid():
            self.set_color(color=(chosen.red(), chosen.green(), chosen.blue()))

    def _show_error(self, *, message: str) -> None:
        self.error_label.setText(message)
        if not self.isVisible():
            self.show()
        self.error_label.setVisible(True)
        self.error_label.show()

    @override
    def accept(self) -> None:
        try:
            new_item = self._registry.add_custom_label(
                canonical_label=self.english_label_edit.text(),
                vi_full=self.vietnamese_label_edit.text(),
                en_short=self.short_english_edit.text(),
                vi_short=self.short_vietnamese_edit.text(),
                category_name=self.category_combo.currentText(),
                color=self._selected_color,
            )
        except ValueError as err:
            self._show_error(message=str(err))
            return

        self.error_label.clear()
        self.error_label.hide()
        self.created_item = new_item
        if self._on_label_added is not None:
            self._on_label_added(new_item)
        super().accept()


class MedicalPresetFormDialog(QtWidgets.QDialog):
    """Form UI for creating a new medical terminology preset."""

    _registry: MedicalTerminologyRegistry
    _on_preset_added: Callable[[TerminologyPreset], None] | None

    preset_name_edit: QtWidgets.QLineEdit
    vietnamese_name_edit: QtWidgets.QLineEdit
    error_label: QtWidgets.QLabel
    ok_button: QtWidgets.QPushButton
    cancel_button: QtWidgets.QPushButton
    created_preset: TerminologyPreset | None

    def __init__(
        self,
        *,
        registry: MedicalTerminologyRegistry | None = None,
        on_preset_added: Callable[[TerminologyPreset], None] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._registry = (
            registry if registry is not None else get_terminology_registry()
        )
        self._on_preset_added = on_preset_added
        self.created_preset = None

        title = self.tr("Create Label Preset")
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        self.setMinimumWidth(340)

        self.preset_name_edit = QtWidgets.QLineEdit()
        self.preset_name_edit.setObjectName("preset_name_edit")
        self.preset_name_edit.setPlaceholderText(self.tr("e.g. Brain CT"))

        self.vietnamese_name_edit = QtWidgets.QLineEdit()
        self.vietnamese_name_edit.setObjectName("vietnamese_name_edit")
        self.vietnamese_name_edit.setPlaceholderText(
            self.tr("Localized preset name (Optional)")
        )

        self.error_label = QtWidgets.QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #d93025; font-weight: 500;")
        self.error_label.hide()

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.tr("Preset Name (English) *:"), self.preset_name_edit)
        form_layout.addRow(self.tr("Localized Name:"), self.vietnamese_name_edit)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = button_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.error_label)
        main_layout.addWidget(button_box)

    def _show_error(self, *, message: str) -> None:
        self.error_label.setText(message)
        if not self.isVisible():
            self.show()
        self.error_label.setVisible(True)
        self.error_label.show()

    @override
    def accept(self) -> None:
        try:
            new_preset = self._registry.add_custom_preset(
                preset_name=self.preset_name_edit.text(),
                vi_name=self.vietnamese_name_edit.text(),
            )
        except ValueError as err:
            self._show_error(message=str(err))
            return

        self.error_label.clear()
        self.error_label.hide()
        self._registry.set_active_preset(preset_id=new_preset.preset_id)
        self.created_preset = new_preset
        if self._on_preset_added is not None:
            self._on_preset_added(new_preset)
        super().accept()
