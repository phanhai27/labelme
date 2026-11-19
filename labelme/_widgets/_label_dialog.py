from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable
from collections.abc import Collection
from typing import Final
from typing import Literal
from typing import override

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from .._label_flags import compile_label_flags
from .._label_flags import get_default_flags
from .._medical_terminology import MedicalTerminologyRegistry
from .._medical_terminology import TerminologyItem
from .._medical_terminology import TerminologyPreset
from .._medical_terminology import get_terminology_registry
from ._label_list_widget import LABEL_COLOR_ROLE
from ._label_list_widget import ColorSwatchDelegate
from ._medical_label_dialog import NEW_PRESET_SENTINEL
from ._medical_label_dialog import CategoryFilterComboBox
from ._medical_label_dialog import MedicalLabelFormDialog
from ._medical_label_dialog import MedicalPresetFormDialog
from ._medical_label_dialog import PresetSelectorComboBox

LabelDialogField = Literal["label", "flags", "group_id", "description"]


@dataclasses.dataclass(frozen=True)
class LabelDialogEntry:
    label: str
    flags: dict[str, bool]
    group_id: int | None
    description: str


class _DialogTerminologyListWidgetItem(QtWidgets.QListWidgetItem):
    _owner: LabelDialog

    def __init__(
        self,
        *,
        label: str,
        owner: LabelDialog,
    ) -> None:
        super().__init__(label)
        self._owner = owner
        self.setData(QtCore.Qt.ItemDataRole.UserRole, label)
        self.refresh_display_and_color()

    def refresh_display_and_color(self) -> None:
        canonical = super().data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(canonical, str):
            return
        registry = self._owner.terminology_registry
        term_item = registry.get_item(canonical_label=canonical)
        if term_item is None:
            super().setData(QtCore.Qt.ItemDataRole.DisplayRole, canonical)
        else:
            self.setData(LABEL_COLOR_ROLE, QtGui.QColor(*term_item.color))
            display = registry.get_display_label(
                canonical_label=canonical,
                category_filter_active=self._owner.is_category_filter_active(),
            )
            super().setData(QtCore.Qt.ItemDataRole.DisplayRole, display)

    @override
    def data(self, role: int, /) -> object:
        if role in (
            int(QtCore.Qt.ItemDataRole.DisplayRole),
            int(QtCore.Qt.ItemDataRole.EditRole),
        ):
            canonical = super().data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(canonical, str):
                registry = self._owner.terminology_registry
                if registry.get_item(canonical_label=canonical) is not None:
                    return registry.get_display_label(
                        canonical_label=canonical,
                        category_filter_active=self._owner.is_category_filter_active(),
                    )
        return super().data(role)


class LabelDialog(QtWidgets.QDialog):
    """Dialog for entering label, group id, description, and flags."""

    _sort_labels: bool
    _flags_spec: dict[re.Pattern[str], list[str]]
    _label_history: list[str]
    _predefined_labels: list[str]
    _locked: frozenset[LabelDialogField]
    _last_label: str
    _entry: LabelDialogEntry | None
    _flag_checkboxes: dict[str, QtWidgets.QCheckBox]
    _flag_states: dict[str, bool]
    _stored_flag_names: tuple[str, ...]
    _fit_to_content: dict[str, bool]
    _ok_button: QtWidgets.QPushButton
    _cancel_button: QtWidgets.QPushButton
    _flags_container: QtWidgets.QWidget
    _flags_layout: QtWidgets.QVBoxLayout
    _flags_scroll: QtWidgets.QScrollArea
    _terminology_registry: MedicalTerminologyRegistry
    _on_add_label_requested: Callable[[], object] | None
    _on_preset_changed: Callable[[str], None] | None
    _on_new_preset_requested: Callable[[], object] | None
    _selected_canonical_label: str | None
    _is_selecting_from_list: bool

    edit: QtWidgets.QLineEdit
    edit_group_id: QtWidgets.QLineEdit
    edit_description: QtWidgets.QTextEdit
    label_list: QtWidgets.QListWidget
    preset_combo: PresetSelectorComboBox
    category_combo: CategoryFilterComboBox
    add_label_button: QtWidgets.QToolButton

    def __init__(
        self,
        *,
        text: str | None = None,
        parent: QtWidgets.QWidget | None = None,
        labels: list[str] | None = None,
        sort_labels: bool = True,
        show_text_field: bool = True,
        completion: str = "startswith",
        fit_to_content: dict[str, bool] | None = None,
        flags: dict[str, list[str]] | None = None,
        label_history: list[str] | None = None,
        terminology_registry: MedicalTerminologyRegistry | None = None,
        on_add_label_requested: Callable[[], object] | None = None,
        on_preset_changed: Callable[[str], None] | None = None,
        on_new_preset_requested: Callable[[], object] | None = None,
    ) -> None:
        LABEL_LIST_HEIGHT: Final[int] = 150

        super().__init__(parent)
        dialog_name = self.tr("Shape Label")
        self.setWindowTitle(dialog_name)
        self.setAccessibleName(dialog_name)

        self._terminology_registry = (
            terminology_registry
            if terminology_registry is not None
            else get_terminology_registry()
        )
        self._on_add_label_requested = on_add_label_requested
        self._on_preset_changed = on_preset_changed
        self._on_new_preset_requested = on_new_preset_requested
        self._selected_canonical_label = None
        self._is_selecting_from_list = False

        self._sort_labels = sort_labels
        self._flags_spec = compile_label_flags(label_flags=flags)
        self._label_history = label_history[:] if label_history is not None else []
        self._predefined_labels = list(labels or [])
        # Fields the current popup shows read-only because the caller has no
        # single value for them (a mixed multi-selection).
        self._locked = frozenset()
        # A popup opened without a label starts from the last one accepted.
        self._last_label = ""
        self._entry = None
        self.accepted.connect(self._capture_entry)
        # The flags currently on show, keyed by flag name, so a flag named by
        # two matching label_flags patterns gets exactly one checkbox.
        self._flag_checkboxes = {}
        # Checked state per flag key, remembered for the lifetime of one popup.
        # The checkboxes themselves cannot hold it: editing the label rebuilds
        # them, and an intermediate keystroke that matches no pattern destroys
        # them entirely.
        self._flag_states = {}
        self._stored_flag_names = ()

        if fit_to_content is None:
            fit_to_content = {"row": False, "column": True}
        self._fit_to_content = fit_to_content

        # Build primary focus widgets in strict focus-chain order:
        # edit -> edit_group_id -> _ok_button -> _cancel_button -> label_list
        self.edit = QtWidgets.QLineEdit()
        self.edit.setPlaceholderText(
            self.tr("Enter object label") if text is None else text
        )
        self.edit.setAccessibleName(self.tr("Label"))

        group_id_name = self.tr("Group ID")
        self.edit_group_id = QtWidgets.QLineEdit()
        self.edit_group_id.setPlaceholderText(group_id_name)
        # Wide enough that the placeholder, in any language, is not cut off.
        GROUP_ID_PADDING: Final[int] = 16
        self.edit_group_id.setMinimumWidth(
            self.edit_group_id.fontMetrics().horizontalAdvance(group_id_name)
            + GROUP_ID_PADDING
        )
        self.edit_group_id.setAccessibleName(group_id_name)
        self.edit_group_id.setValidator(
            QtGui.QRegularExpressionValidator(QtCore.QRegularExpression(r"[0-9]*"))
        )

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self._ok_button = button_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        self._cancel_button = button_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.label_list = QtWidgets.QListWidget()
        self.label_list.setFixedHeight(LABEL_LIST_HEIGHT)
        self.label_list.setItemDelegate(ColorSwatchDelegate(parent=self.label_list))

        description_name = self.tr("Description")
        self.edit_description = QtWidgets.QTextEdit()
        self.edit_description.setPlaceholderText(description_name)
        self.edit_description.setAccessibleName(description_name)
        self.edit_description.setFixedHeight(50)

        # Medical terminology navigation controls use ClickFocus so they do not
        # alter the keyboard Tab order between edit, edit_group_id, buttons, and
        # label_list.
        self.preset_combo = PresetSelectorComboBox(registry=self._terminology_registry)
        self.preset_combo.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.preset_combo.setToolTip(self.tr("Select Medical Label Preset"))
        self.preset_combo.currentIndexChanged.connect(self._handle_preset_combo_changed)

        self.category_combo = CategoryFilterComboBox(
            registry=self._terminology_registry
        )
        self.category_combo.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.category_combo.setToolTip(self.tr("Filter by Anatomical Category"))
        self.category_combo.currentIndexChanged.connect(
            self._handle_category_combo_changed
        )

        self.add_label_button = QtWidgets.QToolButton()
        self.add_label_button.setObjectName("add_label_button")
        self.add_label_button.setText("+")
        self.add_label_button.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        self.add_label_button.setToolTip(self.tr("Add New Medical Label…"))
        self.add_label_button.clicked.connect(self._handle_add_label_clicked)

        # Configure label list
        if sort_labels:
            self.label_list.setDragDropMode(
                QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop
            )
        else:
            self.label_list.setDragDropMode(
                QtWidgets.QAbstractItemView.DragDropMode.InternalMove
            )

        if fit_to_content["row"]:
            self.label_list.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
        if fit_to_content["column"]:
            self.label_list.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )

        # Set up completer bound to label_list's model
        completer = self._make_completer(completion=completion)
        self.edit.setCompleter(completer)
        # Up/Down are taken before the line edit sees them so the arrow keys walk
        # the label list while every other key keeps editing the text.
        self.edit.installEventFilter(self)

        # Build layout
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        # Hiding the label text field leaves the label to the list below; the
        # Group ID has no other editor, so it stays.
        top_row = QtWidgets.QHBoxLayout()
        if show_text_field:
            top_row.addWidget(self.edit, stretch=4)
        top_row.addWidget(self.edit_group_id, stretch=1)
        main_layout.addLayout(top_row)

        terminology_row = QtWidgets.QHBoxLayout()
        terminology_row.setContentsMargins(0, 0, 0, 0)
        terminology_row.setSpacing(4)
        terminology_row.addWidget(self.preset_combo, stretch=1)
        terminology_row.addWidget(self.category_combo, stretch=1)
        terminology_row.addWidget(self.add_label_button)
        main_layout.addLayout(terminology_row)

        main_layout.addWidget(button_box)
        main_layout.addWidget(self.label_list)

        self._flags_container = QtWidgets.QWidget()
        self._flags_layout = QtWidgets.QVBoxLayout()
        self._flags_layout.setContentsMargins(0, 0, 0, 0)
        self._flags_layout.setSpacing(0)
        self._flags_container.setLayout(self._flags_layout)

        self._flags_scroll = QtWidgets.QScrollArea()
        self._flags_scroll.setWidgetResizable(True)
        self._flags_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self._flags_scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._flags_scroll.setWidget(self._flags_container)
        main_layout.addWidget(self._flags_scroll)

        main_layout.addWidget(self.edit_description)

        if show_text_field:
            QtWidgets.QWidget.setTabOrder(self.edit, self.edit_group_id)
        QtWidgets.QWidget.setTabOrder(self.edit_group_id, self._ok_button)
        QtWidgets.QWidget.setTabOrder(self._ok_button, self._cancel_button)
        QtWidgets.QWidget.setTabOrder(self._cancel_button, self.label_list)
        QtWidgets.QWidget.setTabOrder(self.label_list, self.edit_description)

        # Connect signals
        self.edit.textChanged.connect(self._on_text_changed)
        self.label_list.itemSelectionChanged.connect(self._select_current_label)
        self.label_list.itemClicked.connect(self._on_label_selected)
        self.label_list.itemDoubleClicked.connect(self._accept_clicked_label)

        # Populate initial labels
        for label in dict.fromkeys([*(labels or []), *self._label_history]):
            self._add_dialog_label_item(label=label)
        if self._should_sort_alphabetically():
            self.label_list.sortItems()

        self._refresh_ok_button()

    @property
    def terminology_registry(self) -> MedicalTerminologyRegistry:
        return self._terminology_registry

    @property
    def label_history(self) -> list[str]:
        return self._label_history[:]

    def is_category_filter_active(self) -> bool:
        return self.category_combo.active_category_id() is not None

    def active_category_id(self) -> str | None:
        return self.category_combo.active_category_id()

    def set_category_filter(
        self,
        *,
        category_id_or_name: str | None,
    ) -> None:
        if not category_id_or_name:
            self.category_combo.setCurrentIndex(0)
            return
        self.category_combo.setCurrentText(category_id_or_name)

    def visible_label_items(self) -> list[QtWidgets.QListWidgetItem]:
        return [
            self.label_list.item(i)
            for i in range(self.label_list.count())
            if not self.label_list.item(i).isHidden()
        ]

    def visible_labels(self) -> list[str]:
        return [
            item.data(QtCore.Qt.ItemDataRole.UserRole) or item.text()
            for item in self.visible_label_items()
        ]

    def _has_medical_items(self) -> bool:
        for i in range(self.label_list.count()):
            item = self.label_list.item(i)
            canonical = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if (
                isinstance(canonical, str)
                and self._terminology_registry.get_item(canonical_label=canonical)
                is not None
            ):
                return True
        return False

    def _should_sort_alphabetically(self) -> bool:
        if not self._sort_labels:
            return False
        if self.label_list.count() == 0:
            return True
        return not all(
            self._terminology_registry.get_item(
                canonical_label=self.label_list.item(i).data(
                    QtCore.Qt.ItemDataRole.UserRole
                )
                or self.label_list.item(i).text()
            )
            is not None
            for i in range(self.label_list.count())
        )

    def _add_dialog_label_item(self, *, label: str) -> _DialogTerminologyListWidgetItem:
        item = _DialogTerminologyListWidgetItem(label=label, owner=self)
        self.label_list.addItem(item)
        return item

    def _find_item_by_canonical(
        self, *, label: str
    ) -> QtWidgets.QListWidgetItem | None:
        for i in range(self.label_list.count()):
            item = self.label_list.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == label:
                return item
        for item in self.label_list.findItems(label, QtCore.Qt.MatchFlag.MatchExactly):
            return item
        return None

    def _handle_preset_combo_changed(self, _index: int, /) -> None:
        data = self.preset_combo.currentData()
        if not isinstance(data, str):
            return
        if data == NEW_PRESET_SENTINEL:
            if self._on_new_preset_requested is None:
                self.open_new_preset_dialog()
            else:
                self._on_new_preset_requested()
            return
        if data == self._terminology_registry.active_preset_id:
            return
        self._terminology_registry.set_active_preset(preset_id=data)
        self.category_combo.refresh_categories(keep_category_id="all")
        if self._on_preset_changed is None:
            self.set_predefined_labels(
                labels=self._terminology_registry.canonical_labels()
            )
        else:
            self._on_preset_changed(data)
        self._apply_category_filter()

    def _handle_category_combo_changed(self, _index: int, /) -> None:
        self._apply_category_filter()

    def _handle_add_label_clicked(self) -> None:
        if self._on_add_label_requested is None:
            self.open_add_label_dialog()
        else:
            self._on_add_label_requested()

    def open_add_label_dialog(self) -> MedicalLabelFormDialog:
        dialog = MedicalLabelFormDialog(
            registry=self._terminology_registry,
            on_label_added=self._on_form_label_added,
            parent=self,
        )
        dialog.exec()
        return dialog

    def open_new_preset_dialog(self) -> MedicalPresetFormDialog:
        prev_id = self._terminology_registry.active_preset_id
        dialog = MedicalPresetFormDialog(
            registry=self._terminology_registry,
            on_preset_added=self._on_form_preset_added,
            parent=self,
        )
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            self.preset_combo.refresh_presets()
            idx = self.preset_combo.findData(prev_id)
            if idx >= 0:
                with QtCore.QSignalBlocker(self.preset_combo):
                    self.preset_combo.setCurrentIndex(idx)
        return dialog

    def _on_form_label_added(self, new_item: TerminologyItem, /) -> None:
        self.category_combo.refresh_categories()
        if self._find_item_by_canonical(label=new_item.canonical_label) is None:
            self._add_dialog_label_item(label=new_item.canonical_label)
        self._apply_category_filter()
        self.edit.setText(
            self._terminology_registry.get_display_label(
                canonical_label=new_item.canonical_label,
                category_filter_active=self.is_category_filter_active(),
            )
        )
        self._selected_canonical_label = new_item.canonical_label

    def _on_form_preset_added(self, new_preset: TerminologyPreset, /) -> None:
        self.preset_combo.refresh_presets()
        self.category_combo.refresh_categories(keep_category_id="all")
        if self._on_preset_changed is None:
            self.set_predefined_labels(labels=new_preset.canonical_labels())
        else:
            self._on_preset_changed(new_preset.preset_id)
        self._apply_category_filter()

    def _apply_category_filter(self) -> None:
        cat_id = self.category_combo.active_category_id()
        for i in range(self.label_list.count()):
            item = self.label_list.item(i)
            if isinstance(item, _DialogTerminologyListWidgetItem):
                item.refresh_display_and_color()
            canonical = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if cat_id is None:
                item.setHidden(False)
            else:
                term_item = (
                    self._terminology_registry.get_item(canonical_label=canonical)
                    if isinstance(canonical, str)
                    else None
                )
                item.setHidden(term_item is None or term_item.category_id != cat_id)
        self.label_list.viewport().update()

    def refresh_locale_display(self) -> None:
        self.preset_combo.refresh_presets()
        self.category_combo.refresh_categories()
        self._apply_category_filter()

    @override
    def changeEvent(self, event: QtCore.QEvent, /) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.refresh_locale_display()

    def _make_completer(self, *, completion: str) -> QtWidgets.QCompleter:
        if completion == "startswith":
            completer = QtWidgets.QCompleter(self.label_list.model())
            completer.setCompletionMode(
                QtWidgets.QCompleter.CompletionMode.InlineCompletion
            )
            return completer
        elif completion == "contains":
            completer = QtWidgets.QCompleter(self.label_list.model())
            completer.setCompletionMode(
                QtWidgets.QCompleter.CompletionMode.PopupCompletion
            )
            completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
            return completer
        else:
            raise ValueError(f"Unknown completion mode: {completion!r}")

    def _on_text_changed(self, text: str, /) -> None:
        # Leading whitespace never belongs to a label, so undo it as it is typed;
        # the re-entrant signal then handles the corrected text.
        if text != text.lstrip():
            self.edit.setText(text.lstrip())
            return
        self._refresh_ok_button()
        if "flags" not in self._locked:
            self._update_flags(text=text)
        if not self._is_selecting_from_list and self._has_medical_items():
            self._filter_medical_items_by_search(query=text)

    def _filter_medical_items_by_search(self, *, query: str) -> None:
        q = query.strip()
        if not q:
            self._selected_canonical_label = None
            self._apply_category_filter()
            return

        cat_id = self.category_combo.active_category_id()
        matching_pairs: list[
            tuple[int, QtWidgets.QListWidgetItem, TerminologyItem]
        ] = []
        for i in range(self.label_list.count()):
            item = self.label_list.item(i)
            canonical = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if not isinstance(canonical, str):
                continue
            term_item = self._terminology_registry.get_item(canonical_label=canonical)
            if term_item is None:
                continue
            if cat_id is not None and term_item.category_id != cat_id:
                continue
            if term_item.matches_query(query=q):
                score = term_item.exact_match_score(query=q)
                matching_pairs.append((score, item, term_item))

        if not matching_pairs:
            self._selected_canonical_label = None
            self._apply_category_filter()
            return

        matched_set = {id(pair[1]) for pair in matching_pairs}
        for i in range(self.label_list.count()):
            item = self.label_list.item(i)
            item.setHidden(id(item) not in matched_set)

        best_score, best_item, best_term = max(matching_pairs, key=lambda pair: pair[0])
        with QtCore.QSignalBlocker(self.label_list):
            self.label_list.setCurrentItem(best_item)
        if best_score > 0 or len(matching_pairs) == 1:
            self._selected_canonical_label = best_term.canonical_label
        else:
            self._selected_canonical_label = None

    def _refresh_ok_button(self) -> None:
        # Return only ever reaches an enabled default button, so disabling OK is
        # what keeps a blank label from being submitted.
        self._ok_button.setEnabled(
            "label" in self._locked or bool(self.edit.text().strip())
        )

    @override
    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent, /) -> bool:
        if watched is not self.edit or event.type() != QtCore.QEvent.Type.KeyPress:
            return super().eventFilter(watched, event)
        assert isinstance(event, QtGui.QKeyEvent)
        if (
            event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter)
            and self.edit.completer().completionMode()
            == QtWidgets.QCompleter.CompletionMode.InlineCompletion
        ):
            # QLineEdit can retain an inline suggestion from an earlier popup.
            self._ok_button.click()
            return True
        actions = {
            QtCore.Qt.Key.Key_Up: QtWidgets.QAbstractItemView.CursorAction.MoveUp,
            QtCore.Qt.Key.Key_Down: QtWidgets.QAbstractItemView.CursorAction.MoveDown,
        }
        action = actions.get(QtCore.Qt.Key(event.key()))
        if action is None:
            return super().eventFilter(watched, event)

        index = self.label_list.moveCursor(action, event.modifiers())
        # At a boundary, even an unselected suggestion must leave typed text alone.
        if index.isValid() and index != self.label_list.currentIndex():
            self.label_list.selectionModel().setCurrentIndex(
                index, self.label_list.selectionCommand(index, event)
            )
        return True

    def _select_current_label(self) -> None:
        # Tabbing into the list sets a current row without selecting a label.
        # Only an explicit selection should replace the typed text.
        item = self.label_list.currentItem()
        if item is not None and item.isSelected():
            self._on_label_selected(item)

    def _on_label_selected(self, item: QtWidgets.QListWidgetItem, /) -> None:
        canonical = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self._selected_canonical_label = (
            canonical if isinstance(canonical, str) else None
        )
        self._is_selecting_from_list = True
        try:
            self.edit.setText(item.text())
        finally:
            self._is_selecting_from_list = False

    def _accept_clicked_label(self, item: QtWidgets.QListWidgetItem, /) -> None:
        self._on_label_selected(item)
        self._ok_button.click()

    def _clear_flag_checkboxes(self) -> None:
        self._flag_checkboxes.clear()
        while self._flags_layout.count():
            item = self._flags_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def set_flag_rules(self, *, flags: dict[str, list[str]] | None) -> None:
        self._flags_spec = compile_label_flags(label_flags=flags)

    def _update_flags(self, *, text: str) -> None:
        if "flags" in self._locked:
            self._set_flag_checkboxes(flags={})
            return
        self._flag_states.update(self._collect_flags())
        flags = get_default_flags(label=text, flags_spec=self._flags_spec)
        # Rules offer defaults; changing the label must not erase stored data.
        for key in (*flags, *self._stored_flag_names):
            flags[key] = self._flag_states.get(key, False)
        self._set_flag_checkboxes(flags=flags)

    def add_label_history(self, *, label: str) -> None:
        if label not in self._label_history:
            self._label_history.append(label)

        if self._find_item_by_canonical(label=label) is not None:
            return
        self._add_dialog_label_item(label=label)
        if self._should_sort_alphabetically():
            self.label_list.sortItems()

    def remove_label(self, *, label: str) -> None:
        if label in self._label_history:
            self._label_history.remove(label)
        if self._last_label == label:
            self._last_label = ""
        for i in reversed(range(self.label_list.count())):
            item = self.label_list.item(i)
            if (
                item.data(QtCore.Qt.ItemDataRole.UserRole) == label
                or item.text() == label
            ):
                self.label_list.takeItem(i)

    def set_predefined_labels(self, *, labels: list[str]) -> None:
        self._predefined_labels = list(labels)
        history_extras = [h for h in self._label_history if h not in labels]
        all_labels = list(dict.fromkeys(labels)) + history_extras

        self.label_list.clear()
        for label in all_labels:
            self._add_dialog_label_item(label=label)

        if self._should_sort_alphabetically():
            self.label_list.sortItems()
        self._apply_category_filter()

    @property
    def last_label(self) -> str:
        return self._last_label

    def remember_label(self, *, label: str) -> None:
        self._last_label = label

    def _find_label_row(self, *, text: str) -> int:
        # Match through the model so the highlight folds case the way Qt's own
        # text matching does; Python's folding differs on the sharp s, say.
        model = self.label_list.model()
        hits = model.match(
            model.index(0, 0),
            QtCore.Qt.ItemDataRole.DisplayRole,
            text,
            flags=QtCore.Qt.MatchFlag.MatchFixedString,
        )
        if hits:
            return hits[0].row()
        cleaned = text.strip().lower()
        if cleaned:
            for i in range(self.label_list.count()):
                item = self.label_list.item(i)
                canonical = item.data(QtCore.Qt.ItemDataRole.UserRole)
                if isinstance(canonical, str) and canonical.lower() == cleaned:
                    return i
        return -1

    def popup(
        self,
        *,
        text: str | None = None,
        flags: dict[str, bool] | None = None,
        group_id: int | None = None,
        description: str | None = None,
        locked: Collection[LabelDialogField] = (),
        move: bool = True,
        position: QtCore.QPoint | None = None,
    ) -> LabelDialogEntry | None:
        self._entry = None
        self._selected_canonical_label = None
        self._locked = frozenset(locked)
        # Seed from the caller's flags and clear the previous popup's checkboxes
        # before changing the label, so its change signal cannot carry checked
        # values over from another Shape.
        self._flag_states = dict(flags or {})
        self._stored_flag_names = tuple(flags or {})
        self._clear_flag_checkboxes()
        self._apply_category_filter()

        # A locked field shows nothing: the caller's value is not shared by the
        # whole selection, and the field is skipped when the entry is applied.
        for name, widgets in self._get_field_widgets().items():
            for widget in widgets:
                widget.setEnabled(name not in self._locked)
        if "label" in self._locked:
            text = ""
        elif text is None:
            text = self._last_label
        if "group_id" in self._locked:
            group_id = None
        if "description" in self._locked:
            description = None
        if "flags" in self._locked:
            flags = {}

        self._is_selecting_from_list = True
        try:
            self.edit.setText(text)
        finally:
            self._is_selecting_from_list = False
        # Read the text back: a stored label with leading whitespace is shown
        # normalized, and the flags and list match must follow what is shown.
        text = self.edit.text()
        self.edit.selectAll()
        self.edit_group_id.setText("" if group_id is None else str(group_id))
        self.edit_description.setPlainText(description or "")
        self._update_flags(text=text)

        # Highlight the suggestion without applying its spelling to the label.
        with QtCore.QSignalBlocker(self.label_list):
            self.label_list.setCurrentRow(self._find_label_row(text=text))

        self._fit_label_list_to_content()
        self._refresh_ok_button()
        if self.edit.parent() is None:
            # Without the label text field, focus opens on a button, as it did
            # before the Group ID field joined the layout: the first keystrokes
            # must not land in Group ID. A blank label disables OK.
            button = (
                self._ok_button if self._ok_button.isEnabled() else self._cancel_button
            )
            button.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
        else:
            self.edit.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)

        if move:
            target = position if position is not None else QtGui.QCursor.pos()
            self._move_within_screen(target=target)
            # frameGeometry() lacks the window-manager decoration size until the
            # dialog is mapped, so re-clamp once exec() has shown it. Clamp only
            # (no re-anchor to target): a full re-move visibly jerks the already
            # visible dialog, while the clamp is a no-op unless it overflows.
            QtCore.QTimer.singleShot(
                0, lambda: self._clamp_within_screen(target=target)
            )

        self.exec()
        return self._entry

    def _resolve_output_label(self, *, raw_text: str) -> str:
        if not raw_text:
            return ""
        if not self._has_medical_items():
            return raw_text
        cat_id = self.category_combo.active_category_id()
        if self._selected_canonical_label is not None:
            sel_item = self._terminology_registry.get_item(
                canonical_label=self._selected_canonical_label
            )
            if sel_item is not None and sel_item.matches_query(query=raw_text):
                return sel_item.canonical_label
        return self._terminology_registry.resolve_canonical_label(
            input_text=raw_text, category_id=cat_id
        )

    def _capture_entry(self) -> None:
        # The flag checkboxes follow the text, so normalize it before they are
        # collected: "cat " must yield the flags of "cat", not none.
        raw_text = self.edit.text().strip()
        canonical_label = self._resolve_output_label(raw_text=raw_text)
        self._is_selecting_from_list = True
        try:
            self.edit.setText(canonical_label)
        finally:
            self._is_selecting_from_list = False
        group_id_text = self.edit_group_id.text()
        self._entry = LabelDialogEntry(
            label=canonical_label,
            flags=self._collect_flags(),
            group_id=int(group_id_text) if group_id_text else None,
            description=self.edit_description.toPlainText(),
        )
        # A locked label is accepted as blank, and the next new-shape popup
        # starts blank too, exactly as a cancelled locked edit leaves it.
        self.remember_label(label=self._entry.label)

    def _get_field_widgets(
        self,
    ) -> dict[LabelDialogField, tuple[QtWidgets.QWidget, ...]]:
        return {
            "label": (self.edit, self.label_list),
            "flags": (self._flags_container,),
            "group_id": (self.edit_group_id,),
            "description": (self.edit_description,),
        }

    def _set_flag_checkboxes(self, *, flags: dict[str, bool]) -> None:
        FLAGS_SCROLL_MAX_HEIGHT: Final[int] = 150

        self._clear_flag_checkboxes()
        for key, checked in flags.items():
            checkbox = QtWidgets.QCheckBox(key)
            checkbox.setChecked(checked)
            self._flag_checkboxes[key] = checkbox
            self._flags_layout.addWidget(checkbox)
            # A widget added to a visible layout stays hidden until the event
            # loop activates the layout, and the layout counts hidden widgets as
            # empty, so the container hint below would be momentarily 0 and
            # would pin the scroll area shut for the rest of the popup.
            checkbox.show()

        content_height = self._flags_container.sizeHint().height()
        self._flags_scroll.setFixedHeight(min(content_height, FLAGS_SCROLL_MAX_HEIGHT))

    def _collect_flags(self) -> dict[str, bool]:
        return {key: cb.isChecked() for key, cb in self._flag_checkboxes.items()}

    def _fit_label_list_to_content(self) -> None:
        if self._fit_to_content["row"]:
            self.label_list.setMinimumHeight(
                self.label_list.sizeHintForRow(0) * self.label_list.count() + 2
            )
        if self._fit_to_content["column"]:
            self.label_list.setMinimumWidth(self.label_list.sizeHintForColumn(0) + 2)

    def _move_within_screen(self, *, target: QtCore.QPoint) -> None:
        self.adjustSize()
        # setGeometry() anchors the client area, unlike move() which anchors the
        # window frame: the content corner lands at target, not the title bar's.
        self.setGeometry(QtCore.QRect(target, self.size()))
        self._clamp_within_screen(target=target)

    def _clamp_within_screen(self, *, target: QtCore.QPoint) -> None:
        screen = (
            QtGui.QGuiApplication.screenAt(target)
            or QtGui.QGuiApplication.primaryScreen()
        )
        if screen is None:
            return
        available = screen.availableGeometry()

        # Nudge by the actual frame overflow (frameGeometry() includes the
        # window-manager decoration) so the title bar and borders stay on screen,
        # not just the content rect.
        frame = self.frameGeometry()
        dx = min(0, available.right() - frame.right())
        dx = max(dx, available.left() - frame.left())
        dy = min(0, available.bottom() - frame.bottom())
        dy = max(dy, available.top() - frame.top())
        if dx or dy:
            self.move(self.x() + dx, self.y() + dy)
