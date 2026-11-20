from __future__ import annotations

import contextlib
from collections.abc import Callable
from collections.abc import Container
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Final
from typing import override

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from .._medical_terminology import MedicalTerminologyRegistry
from .._medical_terminology import TerminologyItem
from .._medical_terminology import get_terminology_registry
from ._label_list_widget import LABEL_COLOR_ROLE
from ._label_list_widget import ColorSwatchDelegate
from ._medical_label_dialog import CategoryFilterComboBox
from ._medical_label_dialog import MedicalLabelFormDialog


class _EscapableQListWidget(QtWidgets.QListWidget):
    @override
    def keyPressEvent(self, keyEvent: QtGui.QKeyEvent, /) -> None:
        super().keyPressEvent(keyEvent)
        if keyEvent.key() == Qt.Key.Key_Escape:
            self.clearSelection()


# The next free role after the swatch color.
_UNUSED_ROLE: Final = LABEL_COLOR_ROLE + 1


class _LabelDelegate(ColorSwatchDelegate):
    @override
    def sizeHint(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        /,
    ) -> QtCore.QSize:
        size = super().sizeHint(option, index)
        if option.widget is not None:
            size.setWidth(0)
        return size

    @override
    def initStyleOption(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        /,
    ) -> None:
        super().initStyleOption(option, index)
        # Read the palette at paint time, so the dimming follows the theme.
        if index.data(_UNUSED_ROLE):
            option.palette.setColor(
                QtGui.QPalette.ColorRole.Text,
                option.palette.color(QtGui.QPalette.ColorRole.PlaceholderText),
            )


class _TerminologyListWidgetItem(QtWidgets.QListWidgetItem):
    _owner: UniqueLabelQListWidget

    def __init__(
        self,
        *,
        label: str,
        color: tuple[int, int, int],
        owner: UniqueLabelQListWidget,
    ) -> None:
        super().__init__(label)
        self._owner = owner
        self.setData(Qt.ItemDataRole.UserRole, label)
        self.setData(LABEL_COLOR_ROLE, QtGui.QColor(*color))
        self.refresh_display_text()

    def refresh_display_text(self) -> None:
        canonical = super().data(Qt.ItemDataRole.UserRole)
        if isinstance(canonical, str):
            display = self._owner.terminology_registry.get_display_label(
                canonical_label=canonical,
                category_filter_active=self._owner.is_category_filter_active(),
            )
            super().setData(Qt.ItemDataRole.DisplayRole, display)

    @override
    def data(self, role: int, /) -> object:
        if role in (
            int(Qt.ItemDataRole.DisplayRole),
            int(Qt.ItemDataRole.EditRole),
        ):
            canonical = super().data(Qt.ItemDataRole.UserRole)
            if isinstance(canonical, str):
                registry = self._owner.terminology_registry
                if registry.get_item(canonical_label=canonical) is not None:
                    return registry.get_display_label(
                        canonical_label=canonical,
                        category_filter_active=self._owner.is_category_filter_active(),
                    )
        return super().data(role)


def _section_header(
    *,
    title: str,
    buttons: list[QtWidgets.QToolButton],
    extra_row: QtWidgets.QLayout | None = None,
) -> QtWidgets.QWidget:
    header = QtWidgets.QWidget()
    title_label = QtWidgets.QLabel(title)
    title_label.setForegroundRole(QtGui.QPalette.ColorRole.PlaceholderText)
    # Weight and size, not just color, so a header never reads as a label row.
    font = title_label.font()
    font.setWeight(QtGui.QFont.Weight.DemiBold)
    font.setPointSizeF(font.pointSizeF() - 1)
    title_label.setFont(font)

    outer = QtWidgets.QVBoxLayout(header)
    outer.setContentsMargins(4, 2, 4, 2)
    outer.setSpacing(2)

    top_row = QtWidgets.QHBoxLayout()
    top_row.setContentsMargins(0, 0, 0, 0)
    top_row.addWidget(title_label)
    top_row.addStretch(1)
    for button in buttons:
        top_row.addWidget(button)
    outer.addLayout(top_row)

    if extra_row is not None:
        outer.addLayout(extra_row)
    return header


def _header_button(*, text: str, on_click: Callable[[], None]) -> QtWidgets.QToolButton:
    button = QtWidgets.QToolButton()
    button.setText(text)
    button.setAutoRaise(True)
    button.clicked.connect(on_click)
    return button


class UniqueLabelQListWidget(_EscapableQListWidget):
    """Lists the labels from Settings first, then the ones found in annotations.

    Each section sits under a header row. Header rows are disabled, so they
    take no selection and the arrow keys skip them, and they carry no text, so
    the AI prompt's completer, which reads this model, never suggests them.
    """

    label_remove_requested = QtCore.Signal(str)

    _label_set_header: QtWidgets.QListWidgetItem
    _found_header: QtWidgets.QListWidgetItem
    _clear_unused_button: QtWidgets.QToolButton
    _terminology_registry: MedicalTerminologyRegistry
    _on_add_label_requested: Callable[[], object] | None
    _on_edit_label_requested: Callable[[str], object] | None
    _on_delete_label_requested: Callable[[str], object] | None

    category_combo: CategoryFilterComboBox
    add_label_button: QtWidgets.QPushButton
    edit_label_button: QtWidgets.QPushButton
    delete_label_button: QtWidgets.QPushButton

    def __init__(
        self,
        *,
        on_edit_settings_labels: Callable[[], None],
        on_clear_unused: Callable[[], None],
        terminology_registry: MedicalTerminologyRegistry | None = None,
        on_add_label_requested: Callable[[], object] | None = None,
        on_edit_label_requested: Callable[[str], object] | None = None,
        on_delete_label_requested: Callable[[str], object] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self._terminology_registry = (
            terminology_registry
            if terminology_registry is not None
            else get_terminology_registry()
        )
        self._on_add_label_requested = on_add_label_requested
        self._on_edit_label_requested = on_edit_label_requested
        self._on_delete_label_requested = on_delete_label_requested

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setItemDelegate(_LabelDelegate(parent=self))

        self.category_combo = CategoryFilterComboBox(
            registry=self._terminology_registry
        )
        self.category_combo.setToolTip(self.tr("Filter by Anatomical Category"))
        self.category_combo.currentIndexChanged.connect(
            self._handle_category_combo_changed
        )

        # QPushButton so header.findChild(QToolButton) continues to return the
        # "Edit…" QToolButton in existing unit and E2E tests.
        self.add_label_button = QtWidgets.QPushButton("+")
        self.add_label_button.setObjectName("add_label_button")
        self.add_label_button.setFixedWidth(22)
        self.add_label_button.setToolTip(self.tr("Add New Medical Label…"))
        self.add_label_button.clicked.connect(self._handle_add_label_clicked)

        self.edit_label_button = QtWidgets.QPushButton("✎")
        self.edit_label_button.setObjectName("edit_label_button")
        self.edit_label_button.setFixedWidth(22)
        self.edit_label_button.setToolTip(self.tr("Edit Selected Medical Label…"))
        self.edit_label_button.clicked.connect(self._handle_edit_label_clicked)

        self.delete_label_button = QtWidgets.QPushButton("-")
        self.delete_label_button.setObjectName("delete_label_button")
        self.delete_label_button.setFixedWidth(22)
        self.delete_label_button.setToolTip(self.tr("Delete Selected Medical Label"))
        self.delete_label_button.clicked.connect(self._handle_delete_label_clicked)

        controls_row = QtWidgets.QHBoxLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(2)
        controls_row.addWidget(self.category_combo, stretch=1)
        controls_row.addWidget(self.add_label_button)
        controls_row.addWidget(self.edit_label_button)
        controls_row.addWidget(self.delete_label_button)

        self._label_set_header = self._add_header(
            title=self.tr("Label set"),
            buttons=[
                _header_button(text=self.tr("Edit…"), on_click=on_edit_settings_labels)
            ],
            extra_row=controls_row,
        )
        self._clear_unused_button = _header_button(
            text=self.tr("Clear Unused"), on_click=on_clear_unused
        )
        self._clear_unused_button.setEnabled(False)
        self._found_header = self._add_header(
            title=self.tr("Found in files"),
            buttons=[self._clear_unused_button],
        )

    @property
    def terminology_registry(self) -> MedicalTerminologyRegistry:
        return self._terminology_registry

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

    def _add_header(
        self,
        *,
        title: str,
        buttons: list[QtWidgets.QToolButton],
        extra_row: QtWidgets.QLayout | None = None,
    ) -> QtWidgets.QListWidgetItem:
        widget = _section_header(title=title, buttons=buttons, extra_row=extra_row)
        item = QtWidgets.QListWidgetItem()
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setData(Qt.ItemDataRole.AccessibleTextRole, title)
        hint = widget.sizeHint()
        item.setSizeHint(QtCore.QSize(0, hint.height()))
        self.addItem(item)
        self.setItemWidget(item, widget)
        return item

    def selected_canonical_label(self) -> str | None:
        for item in self.selectedItems():
            canonical = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(canonical, str):
                return canonical
        current = self.currentItem()
        if current is not None:
            canonical = current.data(Qt.ItemDataRole.UserRole)
            if isinstance(canonical, str):
                return canonical
        visible = self.visible_label_items()
        if visible:
            canonical = visible[0].data(Qt.ItemDataRole.UserRole)
            if isinstance(canonical, str):
                return canonical
        return None

    def _handle_category_combo_changed(self, _index: int, /) -> None:
        self._apply_category_filter()

    def _handle_add_label_clicked(self) -> None:
        if self._on_add_label_requested is None:
            self.open_add_label_dialog()
        else:
            self._on_add_label_requested()

    def _handle_edit_label_clicked(self) -> None:
        canonical = self.selected_canonical_label()
        if not canonical:
            return
        if self._on_edit_label_requested is None:
            self.open_edit_label_dialog(canonical_label=canonical)
        else:
            self._on_edit_label_requested(canonical)

    def _handle_delete_label_clicked(self) -> None:
        canonical = self.selected_canonical_label()
        if not canonical:
            return
        if self._on_delete_label_requested is None:
            self.delete_medical_label(canonical_label=canonical)
        else:
            self._on_delete_label_requested(canonical)

    def open_add_label_dialog(self) -> MedicalLabelFormDialog:
        dialog = MedicalLabelFormDialog(
            registry=self._terminology_registry,
            on_label_added=self._on_form_label_added,
            on_category_added=lambda _cat: self.category_combo.refresh_categories(),
            on_category_updated=lambda _old,
            _cat: self._refresh_after_category_change(),
            on_category_deleted=lambda _cat: self._refresh_after_category_change(),
            parent=self,
        )
        dialog.exec()
        return dialog

    def open_edit_label_dialog(
        self, *, canonical_label: str | None = None
    ) -> MedicalLabelFormDialog | None:
        target = canonical_label or self.selected_canonical_label()
        if not target:
            return None
        term_item = self._terminology_registry.get_item(canonical_label=target)
        if term_item is None:
            return None
        dialog = MedicalLabelFormDialog(
            registry=self._terminology_registry,
            editing_item=term_item,
            on_label_updated=self._on_form_label_updated,
            on_category_added=lambda _cat: self.category_combo.refresh_categories(),
            on_category_updated=lambda _old,
            _cat: self._refresh_after_category_change(),
            on_category_deleted=lambda _cat: self._refresh_after_category_change(),
            parent=self,
        )
        dialog.exec()
        return dialog

    def delete_medical_label(self, *, canonical_label: str | None = None) -> bool:
        target = canonical_label or self.selected_canonical_label()
        if not target:
            return False
        term_item = self._terminology_registry.get_item(canonical_label=target)
        if term_item is None:
            return False
        display = self._terminology_registry.get_display_label(
            canonical_label=term_item.canonical_label,
            category_filter_active=False,
        )
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg.setWindowTitle(self.tr("Delete Medical Label"))
        msg.setText(
            self.tr("Are you sure you want to delete label '{label}'?").format(
                label=display
            )
        )
        msg.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        if msg.exec() != int(QtWidgets.QMessageBox.StandardButton.Yes):
            return False

        removed = self._terminology_registry.delete_label(
            canonical_label=term_item.canonical_label
        )
        item = self.find_label_item(label=removed.canonical_label)
        if item is not None:
            self.takeItem(self.row(item))
        self._apply_category_filter()
        return True

    def _refresh_after_category_change(self) -> None:
        self.category_combo.refresh_categories()
        valid_canonicals = set(self._terminology_registry.canonical_labels())
        for row in reversed(range(1, self.row(self._found_header))):
            item = self.item(row)
            canonical = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(canonical, str) and canonical not in valid_canonicals:
                self.takeItem(row)
        self._apply_category_filter()

    def _on_form_label_added(self, new_item: TerminologyItem, /) -> None:
        self.category_combo.refresh_categories()
        if self.find_label_item(label=new_item.canonical_label) is None:
            self.add_label_item(
                label=new_item.canonical_label,
                color=new_item.color,
                from_settings=True,
            )
        self._apply_category_filter()

    def _on_form_label_updated(
        self, old_canonical: str, new_item: TerminologyItem, /
    ) -> None:
        self.category_combo.refresh_categories()
        item = self.find_label_item(label=old_canonical)
        if item is not None:
            item.setData(Qt.ItemDataRole.UserRole, new_item.canonical_label)
            item.setData(LABEL_COLOR_ROLE, QtGui.QColor(*new_item.color))
            if isinstance(item, _TerminologyListWidgetItem):
                item.refresh_display_text()
        self._apply_category_filter()

    @override
    def contextMenuEvent(self, event: QtGui.QContextMenuEvent, /) -> None:
        item = self.itemAt(event.pos())
        if item is None:
            return
        canonical = item.data(Qt.ItemDataRole.UserRole)
        if (
            not isinstance(canonical, str)
            or self._terminology_registry.get_item(canonical_label=canonical) is None
        ):
            return
        self.setCurrentItem(item)
        menu = QtWidgets.QMenu(self)
        edit_act = menu.addAction(self.tr("Edit Medical Label…"))
        del_act = menu.addAction(self.tr("Delete Medical Label"))
        chosen = menu.exec(event.globalPos())  # ty: ignore[invalid-argument-type]
        if chosen is edit_act:
            self._handle_edit_label_clicked()
        elif chosen is del_act:
            self._handle_delete_label_clicked()

    def _apply_category_filter(self) -> None:
        cat_id = self.category_combo.active_category_id()
        for item in self._label_items():
            if isinstance(item, _TerminologyListWidgetItem):
                item.refresh_display_text()
            canonical = item.data(Qt.ItemDataRole.UserRole)
            if cat_id is None:
                item.setHidden(False)
            else:
                term_item = (
                    self._terminology_registry.get_item(canonical_label=canonical)
                    if isinstance(canonical, str)
                    else None
                )
                item.setHidden(term_item is None or term_item.category_id != cat_id)
        self.viewport().update()

    def refresh_locale_display(self) -> None:
        self.category_combo.refresh_categories()
        self._apply_category_filter()

    @override
    def changeEvent(self, event: QtCore.QEvent, /) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self.refresh_locale_display()

    @override
    def indexAt(self, p: QtCore.QPoint, /) -> QtCore.QModelIndex:
        v_rect = self.viewport().rect()
        if p.y() == v_rect.bottom() and p.x() in (
            v_rect.left(),
            v_rect.right(),
        ):
            return QtCore.QModelIndex()
        return super().indexAt(p)

    @override
    def itemAt(self, *args: object) -> QtWidgets.QListWidgetItem | None:
        if len(args) == 1 and isinstance(args[0], QtCore.QPoint):
            pt = args[0]
        elif (
            len(args) == 2  # noqa: PLR2004
            and isinstance(args[0], int)
            and isinstance(args[1], int)
        ):
            pt = QtCore.QPoint(args[0], args[1])
        else:
            return None
        index = self.indexAt(pt)
        return self.itemFromIndex(index) if index.isValid() else None

    @override
    def mousePressEvent(self, mouseEvent: QtGui.QMouseEvent, /) -> None:
        super().mousePressEvent(mouseEvent)
        if not self.indexAt(mouseEvent.position().toPoint()).isValid():
            self.clearSelection()

    @override
    def event(self, event: QtCore.QEvent, /) -> bool:
        if (
            event.type() == QtCore.QEvent.Type.ShortcutOverride
            and isinstance(event, QtGui.QKeyEvent)
            and _is_removal_key(event=event)
        ):
            # The window's Delete Shapes action must not handle list keystrokes.
            event.accept()
            return True
        return super().event(event)

    @override
    def keyPressEvent(self, keyEvent: QtGui.QKeyEvent, /) -> None:
        if not _is_removal_key(event=keyEvent):
            super().keyPressEvent(keyEvent)
            return
        found_labels = self.found_labels()
        for item in self.selectedItems():
            label = item.data(Qt.ItemDataRole.UserRole)
            if label in found_labels:
                self.label_remove_requested.emit(label)

    def _label_items(self) -> list[QtWidgets.QListWidgetItem]:
        return [
            item
            for row in range(self.count())
            if (item := self.item(row)).data(Qt.ItemDataRole.UserRole) is not None
        ]

    def visible_label_items(self) -> list[QtWidgets.QListWidgetItem]:
        return [item for item in self._label_items() if not item.isHidden()]

    def visible_labels(self) -> list[str]:
        return [
            item.data(Qt.ItemDataRole.UserRole) for item in self.visible_label_items()
        ]

    def labels(self) -> list[str]:
        return [item.data(Qt.ItemDataRole.UserRole) for item in self._label_items()]

    def settings_labels(self) -> list[str]:
        return [
            self.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(1, self.row(self._found_header))
            if self.item(row).data(Qt.ItemDataRole.UserRole) is not None
        ]

    def found_labels(self) -> list[str]:
        return [
            self.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.row(self._found_header) + 1, self.count())
        ]

    def set_unused_labels(self, *, labels: Container[str]) -> None:
        # Dimmed rows preview what Clear Unused removes, so only labels found
        # in files dim, including one that just left the label set.
        found_labels = self.found_labels()
        any_unused = False
        for item in self._label_items():
            label = item.data(Qt.ItemDataRole.UserRole)
            unused = label in found_labels and label in labels
            any_unused |= unused
            item.setData(_UNUSED_ROLE, unused)
        self._clear_unused_button.setEnabled(any_unused)

    def label_index(self, *, label: str) -> int:
        # Canvas painting calls this per label per frame, so count rows rather
        # than list the labels. Past the end for an absent label, which is
        # where it would be added.
        HEADER_COUNT: Final = 2
        item = self.find_label_item(label=label)
        if item is None:
            return self.count() - HEADER_COUNT
        row = self.row(item)
        return row - 1 - (row > self.row(self._found_header))

    def find_label_item(self, *, label: str) -> QtWidgets.QListWidgetItem | None:
        for row in range(self.count()):
            item = self.item(row)
            if (
                item is not None
                and item.data(Qt.ItemDataRole.UserRole) is not None
                and item.data(Qt.ItemDataRole.UserRole) == label
            ):
                return item
        return None

    def _create_label_item(
        self, *, label: str, color: tuple[int, int, int]
    ) -> _TerminologyListWidgetItem:
        return _TerminologyListWidgetItem(label=label, color=color, owner=self)

    def add_label_item(
        self,
        *,
        label: str,
        color: tuple[int, int, int],
        from_settings: bool = False,
    ) -> None:
        if self.find_label_item(label=label):
            raise ValueError(f"Item for label '{label}' already exists")
        item = self._create_label_item(label=label, color=color)
        if from_settings:
            self.insertItem(self.row(self._found_header), item)
        else:
            self.addItem(item)
        cat_id = self.category_combo.active_category_id()
        if cat_id is not None:
            term_item = self._terminology_registry.get_item(canonical_label=label)
            item.setHidden(term_item is None or term_item.category_id != cat_id)

    def set_settings_labels(
        self,
        *,
        labels: list[str],
        found_in_annotations: Container[str],
        color: Callable[[str], tuple[int, int, int]],
    ) -> None:
        with self._keeping_selection():
            # A label leaving Settings moves to the end of the annotations
            # section when it was found in annotations, and is removed
            # otherwise.
            for row in reversed(range(1, self.row(self._found_header))):
                label = self.item(row).data(Qt.ItemDataRole.UserRole)
                if label in labels:
                    continue
                item = self.takeItem(row)
                if label in found_in_annotations:
                    self.addItem(item)
            for row, label in enumerate(labels, start=1):
                item = self.find_label_item(label=label)
                if item is None:
                    self.insertItem(
                        row,
                        self._create_label_item(label=label, color=color(label)),
                    )
                elif self.row(item) != row:
                    self.insertItem(row, self.takeItem(self.row(item)))
        self._apply_category_filter()

    def remove_label_items(self, *, labels: Iterable[str]) -> None:
        with self._keeping_selection():
            for label in labels:
                item = self.find_label_item(label=label)
                if item is None:
                    raise ValueError(f"No item for label '{label}'")
                self.takeItem(self.row(item))

    @contextlib.contextmanager
    def _keeping_selection(self) -> Iterator[None]:
        # Moving or removing a row moves Qt's selection to a neighbor, which
        # would become the label new shapes get, so restore it afterwards.
        selected = self.selectedItems()
        current = self.currentItem()
        yield
        self.clearSelection()
        if current is not None and self.row(current) >= 0:
            self.setCurrentItem(
                current, QtCore.QItemSelectionModel.SelectionFlag.NoUpdate
            )
        for item in selected:
            if self.row(item) >= 0:
                item.setSelected(True)


def _is_removal_key(*, event: QtGui.QKeyEvent) -> bool:
    return event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() in (
        Qt.Key.Key_Delete,
        Qt.Key.Key_Backspace,
    )
