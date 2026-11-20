from __future__ import annotations

import copy
import dataclasses
import re
import unicodedata
from typing import Final
from typing import cast

from PySide6 import QtCore


def strip_accents(*, text: str) -> str:
    replaced = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", replaced)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def slugify_identifier(*, text: str) -> str:
    ascii_text = strip_accents(text=text).lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text).strip("_")
    return slug or "custom"


def is_vietnamese_locale(*, locale: str | None = None) -> bool:
    if locale is not None:
        return locale.lower().startswith("vi")
    if QtCore.QCoreApplication.instance() is not None:
        translated = QtCore.QCoreApplication.translate(
            "AiAssistedAnnotationWidget", "Polygon"
        )
        if translated == "Đa giác":
            return True
    return False


@dataclasses.dataclass(frozen=True)
class TerminologyCategory:
    category_id: str
    en_name: str
    vi_name: str

    def display_name(self, *, locale: str | None = None) -> str:
        if is_vietnamese_locale(locale=locale) and self.vi_name:
            return self.vi_name
        return self.en_name or self.category_id

    def to_dict(self) -> dict[str, str]:
        return {
            "category_id": self.category_id,
            "en_name": self.en_name,
            "vi_name": self.vi_name,
        }

    @classmethod
    def from_dict(cls, *, data: dict[str, object]) -> TerminologyCategory:
        cat_id = str(data.get("category_id") or "").strip()
        en_name = str(data.get("en_name") or cat_id).strip()
        vi_name = str(data.get("vi_name") or en_name).strip()
        if not cat_id:
            cat_id = slugify_identifier(text=en_name)
        return cls(category_id=cat_id, en_name=en_name, vi_name=vi_name)


@dataclasses.dataclass(frozen=True)
class TerminologyItem:
    canonical_label: str
    en_full: str
    en_short: str
    vi_full: str
    vi_short: str
    category_id: str
    category_en: str
    category_vi: str
    color: tuple[int, int, int]
    aliases: tuple[str, ...] = ()

    def display_name(self, *, locale: str | None = None, short: bool = False) -> str:
        is_vi = is_vietnamese_locale(locale=locale)
        if is_vi:
            if short:
                return (
                    self.vi_short
                    or self.vi_full
                    or self.en_short
                    or self.canonical_label
                )
            return self.vi_full or self.canonical_label
        if short:
            return self.en_short or self.en_full or self.canonical_label
        return self.en_full or self.canonical_label

    def matches_query(self, *, query: str = "") -> bool:
        q = query.strip().lower()
        if not q:
            return True
        q_ascii = strip_accents(text=q)
        candidates = (
            self.canonical_label,
            self.en_full,
            self.en_short,
            self.vi_full,
            self.vi_short,
            *self.aliases,
        )
        for candidate in candidates:
            if not candidate:
                continue
            cand_lower = candidate.lower()
            if q in cand_lower or q_ascii in strip_accents(text=cand_lower):
                return True
        return False

    def exact_match_score(self, *, query: str = "") -> int:
        q = query.strip().lower()
        if not q:
            return 0
        q_ascii = strip_accents(text=q)
        primary = (
            self.canonical_label.lower(),
            self.en_full.lower(),
            self.vi_full.lower(),
            strip_accents(text=self.vi_full.lower()),
        )
        if q in primary or q_ascii in primary:
            return 3
        secondary = (
            self.en_short.lower(),
            self.vi_short.lower(),
            strip_accents(text=self.vi_short.lower()),
        )
        if q in secondary or q_ascii in secondary:
            return 2
        for alias in self.aliases:
            alias_lower = alias.lower()
            if q == alias_lower or q_ascii == strip_accents(text=alias_lower):
                return 1
        return 0

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_label": self.canonical_label,
            "en_full": self.en_full,
            "en_short": self.en_short,
            "vi_full": self.vi_full,
            "vi_short": self.vi_short,
            "category_id": self.category_id,
            "category_en": self.category_en,
            "category_vi": self.category_vi,
            "color": list(self.color),
            "aliases": list(self.aliases),
        }

    @classmethod
    def from_dict(cls, *, data: dict[str, object]) -> TerminologyItem:
        RGB_LEN: Final[int] = 3
        MAX_RGB: Final[int] = 255

        canonical = str(data.get("canonical_label") or "").strip()
        en_full = str(data.get("en_full") or canonical).strip()
        en_short = str(data.get("en_short") or en_full).strip()
        vi_full = str(data.get("vi_full") or en_full).strip()
        vi_short = str(data.get("vi_short") or vi_full).strip()
        cat_en = str(data.get("category_en") or "General").strip()
        cat_vi = str(data.get("category_vi") or cat_en).strip()
        cat_id = str(data.get("category_id") or slugify_identifier(text=cat_en)).strip()
        raw_color = data.get("color")
        color: tuple[int, int, int] = (255, 165, 0)
        if isinstance(raw_color, list | tuple) and len(raw_color) == RGB_LEN:
            try:
                r = max(0, min(MAX_RGB, int(cast(int, raw_color[0]))))
                g = max(0, min(MAX_RGB, int(cast(int, raw_color[1]))))
                b = max(0, min(MAX_RGB, int(cast(int, raw_color[2]))))
                color = (r, g, b)
            except (TypeError, ValueError):
                pass
        raw_aliases = data.get("aliases")
        aliases: tuple[str, ...] = ()
        if isinstance(raw_aliases, list | tuple):
            aliases = tuple(str(a).strip() for a in raw_aliases if str(a).strip())
        return cls(
            canonical_label=canonical,
            en_full=en_full,
            en_short=en_short,
            vi_full=vi_full,
            vi_short=vi_short,
            category_id=cat_id,
            category_en=cat_en,
            category_vi=cat_vi,
            color=color,
            aliases=aliases,
        )


@dataclasses.dataclass
class TerminologyPreset:
    preset_id: str
    en_name: str
    vi_name: str
    categories: list[TerminologyCategory] = dataclasses.field(default_factory=list)
    items: list[TerminologyItem] = dataclasses.field(default_factory=list)

    def display_name(self, *, locale: str | None = None) -> str:
        if is_vietnamese_locale(locale=locale) and self.vi_name:
            return self.vi_name
        return self.en_name or self.preset_id

    def canonical_labels(self) -> list[str]:
        return [item.canonical_label for item in self.items]

    def to_dict(self) -> dict[str, object]:
        return {
            "preset_id": self.preset_id,
            "en_name": self.en_name,
            "vi_name": self.vi_name,
            "categories": [cat.to_dict() for cat in self.categories],
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, *, data: dict[str, object]) -> TerminologyPreset:
        en_name = str(data.get("en_name") or "Custom").strip()
        vi_name = str(data.get("vi_name") or en_name).strip()
        preset_id = str(
            data.get("preset_id") or slugify_identifier(text=en_name)
        ).strip()
        raw_cats = data.get("categories")
        categories: list[TerminologyCategory] = []
        if isinstance(raw_cats, list):
            for c in raw_cats:
                if isinstance(c, dict):
                    categories.append(
                        TerminologyCategory.from_dict(data=cast(dict[str, object], c))
                    )
        raw_items = data.get("items")
        items: list[TerminologyItem] = []
        if isinstance(raw_items, list):
            for it in raw_items:
                if not isinstance(it, dict):
                    continue
                item = TerminologyItem.from_dict(data=cast(dict[str, object], it))
                if item.canonical_label:
                    items.append(item)
        cat_ids = {c.category_id for c in categories}
        for item in items:
            if item.category_id not in cat_ids:
                categories.append(
                    TerminologyCategory(
                        category_id=item.category_id,
                        en_name=item.category_en,
                        vi_name=item.category_vi,
                    )
                )
                cat_ids.add(item.category_id)
        return cls(
            preset_id=preset_id,
            en_name=en_name,
            vi_name=vi_name,
            categories=categories,
            items=items,
        )


CHEST_XRAY_CATEGORIES: Final[tuple[TerminologyCategory, ...]] = (
    TerminologyCategory(
        category_id="lung_parenchyma",
        en_name="Lung parenchyma",
        vi_name="Nhu mô phổi",
    ),
    TerminologyCategory(
        category_id="pleura",
        en_name="Pleura",
        vi_name="Màng phổi",
    ),
    TerminologyCategory(
        category_id="hilum_mediastinum",
        en_name="Hilum / Mediastinum",
        vi_name="Rốn phổi / trung thất",
    ),
    TerminologyCategory(
        category_id="heart_diaphragm_trachea",
        en_name="Heart / Diaphragm / Trachea",
        vi_name="Tim / cơ hoành / khí quản",
    ),
)

CHEST_XRAY_ITEMS: Final[tuple[TerminologyItem, ...]] = (
    # 1. Lung parenchyma (11 items)
    TerminologyItem(
        canonical_label="Lung opacity",
        en_full="Lung opacity",
        en_short="Opacity",
        vi_full="Đám mờ phổi",
        vi_short="Đám mờ",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(255, 165, 0),
        aliases=(
            "opacity",
            "lung opacity",
            "đám mờ phổi",
            "đám mờ",
            "dam mo phoi",
            "dam mo",
        ),
    ),
    TerminologyItem(
        canonical_label="Consolidation",
        en_full="Consolidation",
        en_short="Consolidation",
        vi_full="Đông đặc phổi",
        vi_short="Đông đặc",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(255, 140, 0),
        aliases=(
            "consolidation",
            "đông đặc phổi",
            "đông đặc",
            "dong dac phoi",
            "dong dac",
        ),
    ),
    TerminologyItem(
        canonical_label="Pulmonary nodule",
        en_full="Pulmonary nodule",
        en_short="Nodule",
        vi_full="Nốt phổi",
        vi_short="Nốt",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(255, 69, 58),
        aliases=(
            "nodule",
            "pulmonary nodule",
            "nốt phổi",
            "nốt",
            "not phoi",
            "not",
        ),
    ),
    TerminologyItem(
        canonical_label="Pulmonary mass",
        en_full="Pulmonary mass",
        en_short="Mass",
        vi_full="Khối phổi",
        vi_short="Khối",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(220, 20, 60),
        aliases=(
            "mass",
            "pulmonary mass",
            "khối phổi",
            "khối",
            "u phổi",
            "khoi phoi",
            "khoi",
            "u phoi",
        ),
    ),
    TerminologyItem(
        canonical_label="Cavity",
        en_full="Cavity",
        en_short="Cavity",
        vi_full="Hang phổi",
        vi_short="Hang",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(255, 99, 71),
        aliases=(
            "cavity",
            "cavitation",
            "hang phổi",
            "hang",
            "hang phoi",
        ),
    ),
    TerminologyItem(
        canonical_label="Pulmonary fibrosis",
        en_full="Pulmonary fibrosis",
        en_short="Fibrosis",
        vi_full="Xơ hóa phổi",
        vi_short="Xơ hóa",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(218, 165, 32),
        aliases=(
            "fibrosis",
            "pulmonary fibrosis",
            "xơ hóa phổi",
            "xơ hóa",
            "xơ phổi",
            "xo hoa phoi",
            "xo hoa",
            "xo phoi",
        ),
    ),
    TerminologyItem(
        canonical_label="Calcification",
        en_full="Calcification",
        en_short="Calcification",
        vi_full="Vôi hóa",
        vi_short="Vôi hóa",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(240, 230, 140),
        aliases=(
            "calcification",
            "vôi hóa",
            "voi hoa",
        ),
    ),
    TerminologyItem(
        canonical_label="Interstitial opacity",
        en_full="Interstitial opacity",
        en_short="Interstitial opacity",
        vi_full="Tổn thương dạng kẽ",
        vi_short="Tổn thương dạng kẽ",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(255, 215, 0),
        aliases=(
            "interstitial opacity",
            "interstitial pattern",
            "tổn thương dạng kẽ",
            "dạng kẽ",
            "ton thuong dang ke",
            "dang ke",
        ),
    ),
    TerminologyItem(
        canonical_label="Atelectasis",
        en_full="Atelectasis",
        en_short="Atelectasis",
        vi_full="Xẹp phổi",
        vi_short="Xẹp",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(205, 92, 92),
        aliases=(
            "atelectasis",
            "lung collapse",
            "collapse",
            "xẹp phổi",
            "xẹp",
            "xep phoi",
            "xep",
        ),
    ),
    TerminologyItem(
        canonical_label="Emphysema",
        en_full="Emphysema",
        en_short="Emphysema",
        vi_full="Khí phế thũng",
        vi_short="Khí phế thũng",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(255, 182, 193),
        aliases=(
            "emphysema",
            "khí phế thũng",
            "khi phe thung",
        ),
    ),
    TerminologyItem(
        canonical_label="Bronchiectasis",
        en_full="Bronchiectasis",
        en_short="Bronchiectasis",
        vi_full="Giãn phế quản",
        vi_short="Giãn phế quản",
        category_id="lung_parenchyma",
        category_en="Lung parenchyma",
        category_vi="Nhu mô phổi",
        color=(255, 105, 180),
        aliases=(
            "bronchiectasis",
            "giãn phế quản",
            "gian phe quan",
        ),
    ),
    # 2. Pleura (5 items)
    TerminologyItem(
        canonical_label="Pleural effusion",
        en_full="Pleural effusion",
        en_short="Effusion",
        vi_full="Tràn dịch màng phổi",
        vi_short="Tràn dịch",
        category_id="pleura",
        category_en="Pleura",
        category_vi="Màng phổi",
        color=(30, 144, 255),
        aliases=(
            "pleural effusion",
            "effusion",
            "tràn dịch màng phổi",
            "tràn dịch",
            "tran dich mang phoi",
            "tran dich",
        ),
    ),
    TerminologyItem(
        canonical_label="Pleural thickening",
        en_full="Pleural thickening",
        en_short="Thickening",
        vi_full="Dày màng phổi",
        vi_short="Dày",
        category_id="pleura",
        category_en="Pleura",
        category_vi="Màng phổi",
        color=(0, 191, 255),
        aliases=(
            "pleural thickening",
            "thickening",
            "dày màng phổi",
            "dày",
            "day mang phoi",
            "day",
        ),
    ),
    TerminologyItem(
        canonical_label="Pneumothorax",
        en_full="Pneumothorax",
        en_short="Pneumothorax",
        vi_full="Tràn khí màng phổi",
        vi_short="Tràn khí",
        category_id="pleura",
        category_en="Pleura",
        category_vi="Màng phổi",
        color=(0, 255, 255),
        aliases=(
            "pneumothorax",
            "tràn khí màng phổi",
            "tràn khí",
            "tran khi mang phoi",
            "tran khi",
        ),
    ),
    TerminologyItem(
        canonical_label="Blunted costophrenic angle",
        en_full="Blunted costophrenic angle",
        en_short="Blunted costophrenic angle",
        vi_full="Tù góc sườn hoành",
        vi_short="Tù góc sườn hoành",
        category_id="pleura",
        category_en="Pleura",
        category_vi="Màng phổi",
        color=(100, 149, 237),
        aliases=(
            "blunted costophrenic angle",
            "costophrenic",
            "tù góc sườn hoành",
            "góc sườn hoành",
            "tu goc suon hoanh",
            "goc suon hoanh",
        ),
    ),
    TerminologyItem(
        canonical_label="Pleural calcification",
        en_full="Pleural calcification",
        en_short="Calcification",
        vi_full="Vôi hóa màng phổi",
        vi_short="Vôi hóa",
        category_id="pleura",
        category_en="Pleura",
        category_vi="Màng phổi",
        color=(135, 206, 250),
        aliases=(
            "pleural calcification",
            "vôi hóa màng phổi",
            "voi hoa mang phoi",
        ),
    ),
    # 3. Hilum / Mediastinum (3 items)
    TerminologyItem(
        canonical_label="Hilar enlargement",
        en_full="Hilar enlargement",
        en_short="Hilar enlargement",
        vi_full="Rốn phổi to",
        vi_short="Rốn phổi to",
        category_id="hilum_mediastinum",
        category_en="Hilum / Mediastinum",
        category_vi="Rốn phổi / trung thất",
        color=(50, 205, 50),
        aliases=(
            "hilar enlargement",
            "rốn phổi to",
            "ron phoi to",
        ),
    ),
    TerminologyItem(
        canonical_label="Hilar or mediastinal lymphadenopathy",
        en_full="Hilar or mediastinal lymphadenopathy",
        en_short="Lymphadenopathy",
        vi_full="Hạch rốn phổi hoặc trung thất to",
        vi_short="Hạch to",
        category_id="hilum_mediastinum",
        category_en="Hilum / Mediastinum",
        category_vi="Rốn phổi / trung thất",
        color=(0, 250, 154),
        aliases=(
            "hilar or mediastinal lymphadenopathy",
            "lymphadenopathy",
            "hạch rốn phổi hoặc trung thất to",
            "hạch rốn phổi",
            "hạch trung thất",
            "hạch to",
            "hach ron phoi",
            "hach to",
        ),
    ),
    TerminologyItem(
        canonical_label="Mediastinal widening",
        en_full="Mediastinal widening",
        en_short="Mediastinal widening",
        vi_full="Trung thất rộng",
        vi_short="Trung thất rộng",
        category_id="hilum_mediastinum",
        category_en="Hilum / Mediastinum",
        category_vi="Rốn phổi / trung thất",
        color=(124, 252, 0),
        aliases=(
            "mediastinal widening",
            "trung thất rộng",
            "trung that rong",
        ),
    ),
    # 4. Heart / Diaphragm / Trachea (2 items)
    TerminologyItem(
        canonical_label="Cardiomegaly",
        en_full="Cardiomegaly",
        en_short="Cardiomegaly",
        vi_full="Tim to",
        vi_short="Tim to",
        category_id="heart_diaphragm_trachea",
        category_en="Heart / Diaphragm / Trachea",
        category_vi="Tim / cơ hoành / khí quản",
        color=(186, 85, 211),
        aliases=(
            "cardiomegaly",
            "tim to",
            "bóng tim to",
            "bong tim to",
        ),
    ),
    TerminologyItem(
        canonical_label="Tracheal shift",
        en_full="Tracheal shift",
        en_short="Tracheal shift",
        vi_full="Di lệch khí quản",
        vi_short="Di lệch khí quản",
        category_id="heart_diaphragm_trachea",
        category_en="Heart / Diaphragm / Trachea",
        category_vi="Tim / cơ hoành / khí quản",
        color=(147, 112, 219),
        aliases=(
            "tracheal shift",
            "tracheal deviation",
            "deviation",
            "di lệch khí quản",
            "di lech khi quan",
        ),
    ),
)

CHEST_XRAY_PRESET: Final[TerminologyPreset] = TerminologyPreset(
    preset_id="chest_xray",
    en_name="Chest X-Ray",
    vi_name="X-quang ngực",
    categories=list(CHEST_XRAY_CATEGORIES),
    items=list(CHEST_XRAY_ITEMS),
)


def validate_canonical_english_label(
    *,
    canonical_label: str,
    existing_labels: list[str] | set[str] | tuple[str, ...] = (),
) -> tuple[bool, str]:
    MIN_PRINTABLE_ASCII: Final[int] = 32

    cleaned = canonical_label.strip()
    if not cleaned:
        return (
            False,
            QtCore.QCoreApplication.translate(
                "MedicalLabelFormDialog",
                "Canonical English label is required for AI JSON storage.",
            ),
        )
    if not cleaned.isascii() or any(ord(ch) < MIN_PRINTABLE_ASCII for ch in cleaned):
        return (
            False,
            QtCore.QCoreApplication.translate(
                "MedicalLabelFormDialog",
                "Canonical English label must use standard English (ASCII) "
                "characters without accents. Enter localized "
                "names in the Localized Display Name field below.",
            ),
        )
    if not any(ch.isalpha() for ch in cleaned):
        return (
            False,
            QtCore.QCoreApplication.translate(
                "MedicalLabelFormDialog",
                "Canonical English label must contain at least one English letter.",
            ),
        )
    existing_lower = {lbl.strip().lower() for lbl in existing_labels}
    if cleaned.lower() in existing_lower:
        return (
            False,
            QtCore.QCoreApplication.translate(
                "MedicalLabelFormDialog",
                "Label '{label}' already exists in the current preset.",
            ).format(label=cleaned),
        )
    return True, ""


def validate_canonical_english_category(
    *,
    en_name: str,
    existing_categories: list[TerminologyCategory]
    | tuple[TerminologyCategory, ...] = (),
) -> tuple[bool, str]:
    MIN_PRINTABLE_ASCII: Final[int] = 32

    cleaned = en_name.strip()
    if not cleaned:
        return (
            False,
            QtCore.QCoreApplication.translate(
                "MedicalCategoryFormDialog",
                "Canonical English category name is required.",
            ),
        )
    if not cleaned.isascii() or any(ord(ch) < MIN_PRINTABLE_ASCII for ch in cleaned):
        return (
            False,
            QtCore.QCoreApplication.translate(
                "MedicalCategoryFormDialog",
                "Canonical English category must use standard English (ASCII) "
                "characters without accents. Enter localized "
                "names in the Localized Display Name field below.",
            ),
        )
    if not any(ch.isalpha() for ch in cleaned):
        return (
            False,
            QtCore.QCoreApplication.translate(
                "MedicalCategoryFormDialog",
                "Canonical English category must contain at least one English letter.",
            ),
        )
    cleaned_lower = cleaned.lower()
    cleaned_slug = slugify_identifier(text=cleaned)
    for cat in existing_categories:
        if (
            cleaned_lower
            in (
                cat.category_id.lower(),
                cat.en_name.lower(),
                cat.vi_name.lower(),
                strip_accents(text=cat.vi_name.lower()),
            )
            or cleaned_slug == cat.category_id.lower()
        ):
            return (
                False,
                QtCore.QCoreApplication.translate(
                    "MedicalCategoryFormDialog",
                    "Category '{category}' already exists in the current preset.",
                ).format(category=cleaned),
            )
    return True, ""


class MedicalTerminologyRegistry:
    _presets: dict[str, TerminologyPreset]
    _custom_added_categories: dict[str, list[TerminologyCategory]]
    _custom_added_items: dict[str, list[TerminologyItem]]
    _custom_presets: dict[str, TerminologyPreset]
    _active_preset_id: str
    _locale: str | None

    def __init__(
        self,
        *,
        active_preset_id: str = "chest_xray",
        custom_config: object = None,
        locale: str | None = None,
    ) -> None:
        self._presets = {}
        self._custom_added_categories = {}
        self._custom_added_items = {}
        self._custom_presets = {}
        self._active_preset_id = "chest_xray"
        self._locale = locale
        self.reset_to_defaults()
        if custom_config is not None:
            self.load_custom_config(data=custom_config)
        if active_preset_id in self._presets:
            self._active_preset_id = active_preset_id

    def reset_to_defaults(self) -> None:
        self._presets = {
            CHEST_XRAY_PRESET.preset_id: TerminologyPreset(
                preset_id=CHEST_XRAY_PRESET.preset_id,
                en_name=CHEST_XRAY_PRESET.en_name,
                vi_name=CHEST_XRAY_PRESET.vi_name,
                categories=list(CHEST_XRAY_PRESET.categories),
                items=list(CHEST_XRAY_PRESET.items),
            )
        }
        self._custom_added_categories = {}
        self._custom_added_items = {}
        self._custom_presets = {}
        self._active_preset_id = CHEST_XRAY_PRESET.preset_id

    @property
    def active_preset_id(self) -> str:
        return self._active_preset_id

    @property
    def active_preset(self) -> TerminologyPreset:
        return self._presets[self._active_preset_id]

    def set_active_preset(self, *, preset_id: str) -> TerminologyPreset:
        if preset_id in self._presets:
            self._active_preset_id = preset_id
            return self._presets[preset_id]
        for pid, preset in self._presets.items():
            if (
                preset.en_name.lower() == preset_id.strip().lower()
                or preset.vi_name.lower() == preset_id.strip().lower()
            ):
                self._active_preset_id = pid
                return preset
        raise ValueError(f"Unknown terminology preset: {preset_id!r}")

    def set_locale(self, *, locale: str | None) -> None:
        self._locale = locale

    def get_locale(self) -> str | None:
        if is_vietnamese_locale(locale=self._locale):
            return "vi_VN"
        return self._locale

    def presets(self) -> list[TerminologyPreset]:
        return list(self._presets.values())

    def get_preset(
        self,
        *,
        preset_id: str | None = None,
    ) -> TerminologyPreset | None:
        target = preset_id or self._active_preset_id
        if target in self._presets:
            return self._presets[target]
        for preset in self._presets.values():
            if (
                preset.en_name.lower() == target.strip().lower()
                or preset.vi_name.lower() == target.strip().lower()
            ):
                return preset
        return None

    def categories(self, *, preset_id: str | None = None) -> list[TerminologyCategory]:
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        return list(preset.categories)

    def resolve_category_id(
        self,
        *,
        category_id_or_name: str | None,
        preset_id: str | None = None,
    ) -> str | None:
        if not category_id_or_name:
            return None
        cleaned = category_id_or_name.strip()
        if cleaned.lower() in (
            "all",
            "tất cả",
            "tat ca",
            "all categories",
            "tất cả nhóm",
        ):
            return None
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        for cat in preset.categories:
            if (
                cat.category_id.lower() == cleaned.lower()
                or cat.en_name.lower() == cleaned.lower()
                or cat.vi_name.lower() == cleaned.lower()
                or strip_accents(text=cat.vi_name.lower())
                == strip_accents(text=cleaned.lower())
            ):
                return cat.category_id
        for cat in preset.categories:
            if (
                cleaned.lower() in cat.en_name.lower()
                or cleaned.lower() in cat.vi_name.lower()
            ):
                return cat.category_id
        return cleaned

    def items(
        self,
        *,
        preset_id: str | None = None,
        category_id: str | None = None,
    ) -> list[TerminologyItem]:
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        resolved_cat = self.resolve_category_id(
            category_id_or_name=category_id, preset_id=preset.preset_id
        )
        if resolved_cat is None:
            return list(preset.items)
        return [item for item in preset.items if item.category_id == resolved_cat]

    def canonical_labels(self, *, preset_id: str | None = None) -> list[str]:
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        return preset.canonical_labels()

    def get_item(
        self,
        *,
        canonical_label: str,
        preset_id: str | None = None,
    ) -> TerminologyItem | None:
        if not canonical_label:
            return None
        target_preset = self.get_preset(preset_id=preset_id) or self.active_preset
        search_presets = [
            target_preset,
            *(p for p in self._presets.values() if p is not target_preset),
        ]
        for preset in search_presets:
            for item in preset.items:
                if item.canonical_label == canonical_label:
                    return item
        lower = canonical_label.strip().lower()
        for preset in search_presets:
            for item in preset.items:
                if item.canonical_label.lower() == lower:
                    return item
        return None

    def get_color(
        self,
        *,
        canonical_label: str,
        preset_id: str | None = None,
    ) -> tuple[int, int, int] | None:
        item = self.get_item(canonical_label=canonical_label, preset_id=preset_id)
        return item.color if item is not None else None

    def suggest_next_color(
        self, *, preset_id: str | None = None
    ) -> tuple[int, int, int]:
        DEFAULT_SUGGESTED_COLORS: Final[tuple[tuple[int, int, int], ...]] = (
            (255, 127, 80),
            (64, 224, 208),
            (255, 215, 0),
            (152, 251, 152),
            (221, 160, 221),
            (240, 128, 128),
            (135, 206, 235),
            (255, 182, 193),
            (173, 255, 47),
            (255, 160, 122),
        )
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        used = {item.color for item in preset.items}
        for color in DEFAULT_SUGGESTED_COLORS:
            if color not in used:
                return color
        return DEFAULT_SUGGESTED_COLORS[
            len(preset.items) % len(DEFAULT_SUGGESTED_COLORS)
        ]

    def get_display_label(
        self,
        *,
        canonical_label: str,
        locale: str | None = None,
        category_filter_active: bool = False,
        preset_id: str | None = None,
    ) -> str:
        item = self.get_item(canonical_label=canonical_label, preset_id=preset_id)
        if item is None:
            return canonical_label
        effective_locale = locale if locale is not None else self._locale
        return item.display_name(locale=effective_locale, short=category_filter_active)

    def resolve_canonical_label(
        self,
        *,
        input_text: str,
        category_id: str | None = None,
        preset_id: str | None = None,
    ) -> str:
        cleaned = input_text.strip()
        if not cleaned:
            return ""
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        resolved_cat = self.resolve_category_id(
            category_id_or_name=category_id, preset_id=preset.preset_id
        )

        # Search active category first if filtered, so ambiguous short names
        # like "Calcification" / "Vôi hóa" in "pleura" resolve to
        # "Pleural calcification" rather than "Calcification" of lung parenchyma.
        ordered_items: list[TerminologyItem] = []
        if resolved_cat is None:
            ordered_items.extend(preset.items)
        else:
            ordered_items.extend(
                it for it in preset.items if it.category_id == resolved_cat
            )
            ordered_items.extend(
                it for it in preset.items if it.category_id != resolved_cat
            )

        for other_preset in self._presets.values():
            if other_preset is not preset:
                ordered_items.extend(other_preset.items)

        best_item: TerminologyItem | None = None
        best_score = 0
        for item in ordered_items:
            score = item.exact_match_score(query=cleaned)
            if (
                resolved_cat is not None
                and item.category_id == resolved_cat
                and score > 0
            ):
                score += 10
            if score > best_score:
                best_score = score
                best_item = item
        if best_item is not None:
            return best_item.canonical_label
        return cleaned

    def filter_items(
        self,
        *,
        query: str = "",
        category_id: str | None = None,
        preset_id: str | None = None,
    ) -> list[TerminologyItem]:
        candidates = self.items(preset_id=preset_id, category_id=category_id)
        q = query.strip()
        if not q:
            return candidates
        return [item for item in candidates if item.matches_query(query=q)]

    def add_custom_category(
        self,
        *,
        en_name: str,
        vi_name: str = "",
        preset_id: str | None = None,
    ) -> TerminologyCategory:
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        valid, error = validate_canonical_english_category(
            en_name=en_name,
            existing_categories=preset.categories,
        )
        if not valid:
            raise ValueError(error)

        cleaned_en = en_name.strip()
        cleaned_vi = vi_name.strip() or cleaned_en
        new_cat = TerminologyCategory(
            category_id=slugify_identifier(text=cleaned_en),
            en_name=cleaned_en,
            vi_name=cleaned_vi,
        )
        preset.categories.append(new_cat)
        if preset.preset_id in self._custom_presets:
            self._custom_presets[preset.preset_id] = preset
        else:
            self._custom_added_categories.setdefault(preset.preset_id, []).append(
                new_cat
            )
        return new_cat

    def add_custom_label(
        self,
        *,
        canonical_label: str,
        vi_full: str = "",
        en_short: str = "",
        vi_short: str = "",
        category_name: str = "",
        color: tuple[int, int, int] | None = None,
        aliases: tuple[str, ...] = (),
        preset_id: str | None = None,
    ) -> TerminologyItem:
        preset = self.get_preset(preset_id=preset_id) or self.active_preset
        valid, error = validate_canonical_english_label(
            canonical_label=canonical_label,
            existing_labels=preset.canonical_labels(),
        )
        if not valid:
            raise ValueError(error)

        cleaned_en = canonical_label.strip()
        cleaned_vi = vi_full.strip() or cleaned_en
        cleaned_en_short = en_short.strip() or cleaned_en
        cleaned_vi_short = vi_short.strip() or cleaned_vi

        cat_input = category_name.strip()
        matched_cat: TerminologyCategory | None = None
        if cat_input:
            for cat in preset.categories:
                if (
                    cat.category_id.lower() == cat_input.lower()
                    or cat.en_name.lower() == cat_input.lower()
                    or cat.vi_name.lower() == cat_input.lower()
                    or strip_accents(text=cat.vi_name.lower())
                    == strip_accents(text=cat_input.lower())
                ):
                    matched_cat = cat
                    break
        if matched_cat is None:
            if cat_input:
                new_cat_id = slugify_identifier(text=cat_input)
                matched_cat = TerminologyCategory(
                    category_id=new_cat_id,
                    en_name=cat_input,
                    vi_name=cat_input,
                )
                preset.categories.append(matched_cat)
                if preset.preset_id not in self._custom_presets:
                    self._custom_added_categories.setdefault(
                        preset.preset_id, []
                    ).append(matched_cat)
            elif preset.categories:
                matched_cat = preset.categories[0]
            else:
                matched_cat = TerminologyCategory(
                    category_id="general",
                    en_name="General",
                    vi_name="Chung",
                )
                preset.categories.append(matched_cat)

        chosen_color = (
            color
            if color is not None
            else self.suggest_next_color(preset_id=preset.preset_id)
        )
        computed_aliases = list(
            dict.fromkeys(
                a.lower()
                for a in (
                    cleaned_en,
                    cleaned_en_short,
                    cleaned_vi,
                    cleaned_vi_short,
                    strip_accents(text=cleaned_vi),
                    strip_accents(text=cleaned_vi_short),
                    *aliases,
                )
                if a.strip()
            )
        )
        new_item = TerminologyItem(
            canonical_label=cleaned_en,
            en_full=cleaned_en,
            en_short=cleaned_en_short,
            vi_full=cleaned_vi,
            vi_short=cleaned_vi_short,
            category_id=matched_cat.category_id,
            category_en=matched_cat.en_name,
            category_vi=matched_cat.vi_name,
            color=chosen_color,
            aliases=tuple(computed_aliases),
        )
        preset.items.append(new_item)
        if preset.preset_id in self._custom_presets:
            self._custom_presets[preset.preset_id] = preset
        else:
            self._custom_added_items.setdefault(preset.preset_id, []).append(new_item)
        return new_item

    def add_custom_preset(
        self,
        *,
        preset_name: str,
        vi_name: str = "",
    ) -> TerminologyPreset:
        cleaned_name = preset_name.strip()
        if not cleaned_name:
            raise ValueError(
                QtCore.QCoreApplication.translate(
                    "MedicalPresetFormDialog",
                    "Preset name cannot be empty.",
                )
            )
        preset_id = slugify_identifier(text=cleaned_name)
        for existing in self._presets.values():
            if (
                existing.preset_id == preset_id
                or existing.en_name.lower() == cleaned_name.lower()
            ):
                raise ValueError(
                    QtCore.QCoreApplication.translate(
                        "MedicalPresetFormDialog",
                        "Preset '{name}' already exists.",
                    ).format(name=cleaned_name)
                )
        new_preset = TerminologyPreset(
            preset_id=preset_id,
            en_name=cleaned_name,
            vi_name=vi_name.strip() or cleaned_name,
            categories=[],
            items=[],
        )
        self._presets[preset_id] = new_preset
        self._custom_presets[preset_id] = new_preset
        return new_preset

    def to_custom_config(self) -> dict[str, object] | None:
        added_categories_dict: dict[str, list[dict[str, str]]] = {}
        for pid, cats in self._custom_added_categories.items():
            if cats:
                added_categories_dict[pid] = [c.to_dict() for c in cats]
        added_items_dict: dict[str, list[dict[str, object]]] = {}
        for pid, items in self._custom_added_items.items():
            if items:
                added_items_dict[pid] = [it.to_dict() for it in items]
        custom_presets_list: list[dict[str, object]] = [
            p.to_dict() for p in self._custom_presets.values()
        ]
        if (
            not added_categories_dict
            and not added_items_dict
            and not custom_presets_list
        ):
            return None
        result: dict[str, object] = {}
        if added_categories_dict:
            result["added_categories"] = copy.deepcopy(added_categories_dict)
        if added_items_dict:
            result["added_items"] = copy.deepcopy(added_items_dict)
        if custom_presets_list:
            result["presets"] = copy.deepcopy(custom_presets_list)
        return result

    def load_custom_config(self, *, data: object) -> None:
        if not isinstance(data, dict):
            return
        data_dict = cast(dict[str, object], data)
        raw_presets = data_dict.get("presets")
        if isinstance(raw_presets, list):
            for p_data in raw_presets:
                if not isinstance(p_data, dict):
                    continue
                preset = TerminologyPreset.from_dict(
                    data=cast(dict[str, object], p_data)
                )
                if preset.preset_id and preset.preset_id != "chest_xray":
                    self._presets[preset.preset_id] = preset
                    self._custom_presets[preset.preset_id] = preset
        raw_added_cats = data_dict.get("added_categories")
        if isinstance(raw_added_cats, dict):
            added_cats_dict = cast(dict[object, object], raw_added_cats)
            for pid, cats_list in added_cats_dict.items():
                if not isinstance(pid, str) or not isinstance(cats_list, list):
                    continue
                target_preset = self._presets.get(pid)
                if target_preset is None:
                    continue
                existing_cats = {
                    c.category_id.lower() for c in target_preset.categories
                }
                for c_data in cats_list:
                    if not isinstance(c_data, dict):
                        continue
                    cat = TerminologyCategory.from_dict(
                        data=cast(dict[str, object], c_data)
                    )
                    if not cat.category_id or cat.category_id.lower() in existing_cats:
                        continue
                    target_preset.categories.append(cat)
                    existing_cats.add(cat.category_id.lower())
                    self._custom_added_categories.setdefault(pid, []).append(cat)
        raw_added = data_dict.get("added_items")
        if not isinstance(raw_added, dict):
            return
        added_dict = cast(dict[object, object], raw_added)
        for pid, items_list in added_dict.items():
            if not isinstance(pid, str) or not isinstance(items_list, list):
                continue
            target_preset = self._presets.get(pid)
            if target_preset is None:
                continue
            existing_labels = {it.canonical_label.lower() for it in target_preset.items}
            existing_cats = {c.category_id for c in target_preset.categories}
            for it_data in items_list:
                if not isinstance(it_data, dict):
                    continue
                item = TerminologyItem.from_dict(data=cast(dict[str, object], it_data))
                if (
                    not item.canonical_label
                    or item.canonical_label.lower() in existing_labels
                ):
                    continue
                if item.category_id not in existing_cats:
                    new_cat = TerminologyCategory(
                        category_id=item.category_id,
                        en_name=item.category_en,
                        vi_name=item.category_vi,
                    )
                    target_preset.categories.append(new_cat)
                    existing_cats.add(item.category_id)
                target_preset.items.append(item)
                existing_labels.add(item.canonical_label.lower())
                self._custom_added_items.setdefault(pid, []).append(item)


_REGISTRY_HOLDER: Final[list[MedicalTerminologyRegistry]] = [
    MedicalTerminologyRegistry()
]


def get_terminology_registry() -> MedicalTerminologyRegistry:
    return _REGISTRY_HOLDER[0]


def set_terminology_registry(
    *, registry: MedicalTerminologyRegistry
) -> MedicalTerminologyRegistry:
    _REGISTRY_HOLDER[0] = registry
    return registry
