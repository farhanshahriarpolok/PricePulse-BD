"""
Taxonomy resolution, bilingual entity mapping, and metric unit normalization.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
from app.core.config import settings


@dataclass(frozen=True)
class NormalizedCommodity:
    canonical_name: str
    bangla_name: str
    category: str
    default_unit: str
    match_weight: float


class CommodityNormalizer:
    """Bilingual normalizer resolving localized commodity labels and metric units."""

    # Unit conversion rules: mapping to (base_unit, multiplier_to_base)
    # Price per base unit = raw_price / multiplier_to_base
    UNIT_MAP: dict[str, Tuple[str, float]] = {
        # Mass units -> kg
        "kg": ("kg", 1.0),
        "কেজি": ("kg", 1.0),
        "কিলোগ্রাম": ("kg", 1.0),
        "kilogram": ("kg", 1.0),
        "kgs": ("kg", 1.0),
        "মণ": ("kg", 40.0),
        "মন": ("kg", 40.0),
        "maund": ("kg", 40.0),
        "mon": ("kg", 40.0),
        "সের": ("kg", 0.933),
        "seer": ("kg", 0.933),
        "sher": ("kg", 0.933),
        "কুইন্টাল": ("kg", 100.0),
        "quintal": ("kg", 100.0),
        "গ্রাম": ("kg", 0.001),
        "gram": ("kg", 0.001),
        "gm": ("kg", 0.001),
        "g": ("kg", 0.001),

        # Volume units -> liter
        "liter": ("liter", 1.0),
        "litre": ("liter", 1.0),
        "লিটার": ("liter", 1.0),
        "লিঃ": ("liter", 1.0),
        "ltr": ("liter", 1.0),
        "l": ("liter", 1.0),
        "মিলিলিটার": ("liter", 0.001),
        "মিলি": ("liter", 0.001),
        "ml": ("liter", 0.001),
        "milliliter": ("liter", 0.001),

        # Count units -> pc
        "piece": ("pc", 1.0),
        "pc": ("pc", 1.0),
        "pcs": ("pc", 1.0),
        "পিস": ("pc", 1.0),
        "টি": ("pc", 1.0),
        "টা": ("pc", 1.0),
        "হালি": ("pc", 4.0),
        "hali": ("pc", 4.0),
        "ডজন": ("pc", 12.0),
        "dozen": ("pc", 12.0),
        "doz": ("pc", 12.0),
        "হাফডজন": ("pc", 6.0),
        "halfdozen": ("pc", 6.0),
        "1/2ডজন": ("pc", 6.0),
        "1/2dozen": ("pc", 6.0),
        "0.5ডজন": ("pc", 6.0),
        "0.5dozen": ("pc", 6.0),
        "১/২ডজন": ("pc", 6.0),
        "০.৫ডজন": ("pc", 6.0),
    }

    def reload(self) -> None:
        """Clear and re-read taxonomy seeds from disk."""
        self._alias_index.clear()
        self._canonical_list.clear()
        self._load_taxonomy()

    def __init__(self, taxonomy_file: Optional[Path] = None):
        self.taxonomy_file = taxonomy_file or (settings.taxonomy_dir / "commodities.json")
        self._alias_index: dict[str, NormalizedCommodity] = {}
        self._canonical_list: list[NormalizedCommodity] = []
        self._load_taxonomy()

    def _clean_text(self, text: str) -> str:
        """Standardize Unicode, diacritics, and whitespace."""
        if not text:
            return ""
        # Unicode canonical composition
        normalized = unicodedata.normalize("NFKC", text)
        # Harmonize Bengali Ya variants (U+09AF + U+09BC vs U+09DF)
        normalized = normalized.replace("\u09af\u09bc", "\u09df")
        # Lowercase Latin characters
        normalized = normalized.lower()
        # Collapse multiple spaces and trim punctuation
        normalized = re.sub(r"[\t\r\n]+", " ", normalized)
        normalized = re.sub(r"[\(\)\[\],:\/]+", " ", normalized)
        return " ".join(normalized.split())

    def _load_taxonomy(self) -> None:
        """Index canonical commodities and aliases from JSON."""
        if not self.taxonomy_file.exists():
            return

        with open(self.taxonomy_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            canonical_name = entry["canonical_name"]
            bangla_name = entry["bangla_name"]
            category = entry.get("category", "General")
            default_unit = entry.get("default_unit", "kg")

            base_item = NormalizedCommodity(
                canonical_name=canonical_name,
                bangla_name=bangla_name,
                category=category,
                default_unit=default_unit,
                match_weight=1.0,
            )
            self._canonical_list.append(base_item)

            # Register exact canonical keys
            cleaned_canon = self._clean_text(canonical_name)
            cleaned_bn = self._clean_text(bangla_name)
            self._alias_index[cleaned_canon] = base_item
            self._alias_index[cleaned_bn] = base_item

            # Register aliases
            for alias_obj in entry.get("aliases", []):
                cleaned_alias = self._clean_text(alias_obj["alias"])
                weight = float(alias_obj.get("weight", 0.95))
                aliased_item = NormalizedCommodity(
                    canonical_name=canonical_name,
                    bangla_name=bangla_name,
                    category=category,
                    default_unit=default_unit,
                    match_weight=weight,
                )
                # Keep highest weight if duplicate alias exists
                if (
                    cleaned_alias not in self._alias_index
                    or weight > self._alias_index[cleaned_alias].match_weight
                ):
                    self._alias_index[cleaned_alias] = aliased_item

    def resolve_commodity(self, raw_label: str) -> Optional[NormalizedCommodity]:
        """
        Resolve raw scraped string to a canonical commodity.
        Returns NormalizedCommodity or None if unmapped.
        """
        cleaned = self._clean_text(raw_label)
        if not cleaned:
            return None

        # 1. Exact alias match
        if cleaned in self._alias_index:
            return self._alias_index[cleaned]

        # 2. Tokenized contains match across aliases
        for alias_key, item in self._alias_index.items():
            if alias_key in cleaned or cleaned in alias_key:
                return NormalizedCommodity(
                    canonical_name=item.canonical_name,
                    bangla_name=item.bangla_name,
                    category=item.category,
                    default_unit=item.default_unit,
                    match_weight=round(item.match_weight * 0.85, 4),
                )

        return None

    def normalize_unit(self, raw_unit: str) -> Tuple[str, float]:
        """
        Normalize unit string to canonical base unit and price multiplier.
        Supports compound packaging units such as '5 kg', '500 gm', '2 liter',
        '1 hali', '1/2 dozen', 'হাফ ডজন', '১/২ ডজন'.
        Returns: (base_unit, multiplier_to_base)
        Raises: ValueError if unit is unmapped.
        """
        cleaned = self._clean_text(raw_unit).replace(" ", "")
        if cleaned in self.UNIT_MAP:
            return self.UNIT_MAP[cleaned]

        # Transliterate Bengali numerals to standard ASCII digits
        bn_to_en = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
        trans_raw = raw_unit.translate(bn_to_en).strip().lower()

        # Direct lowercase/transliterated match
        trans_cleaned = self._clean_text(trans_raw).replace(" ", "")
        if trans_cleaned in self.UNIT_MAP:
            return self.UNIT_MAP[trans_cleaned]
        if trans_raw in self.UNIT_MAP:
            return self.UNIT_MAP[trans_raw]

        # Handle colloquial 'half' or 'হাফ' prefix (e.g. 'half dozen', 'হাফ ডজন')
        half_pattern = re.match(r"^(?:half|হাফ)\s*(.+)$", trans_raw)
        if half_pattern:
            unit_part = half_pattern.group(1).strip()
            unit_cleaned = self._clean_text(unit_part).replace(" ", "")
            if unit_cleaned in self.UNIT_MAP:
                base_unit, base_mult = self.UNIT_MAP[unit_cleaned]
                return base_unit, 0.5 * base_mult
            if unit_part in self.UNIT_MAP:
                base_unit, base_mult = self.UNIT_MAP[unit_part]
                return base_unit, 0.5 * base_mult

        # Check for fractional or decimal quantity prefix (e.g. '1/2 dozen', '5 kg', '0.5 dozen')
        fraction_match = re.match(r"^(\d+\s*/\s*\d+|\d+(?:\.\d+)?)\s*(.+)$", trans_raw)
        if fraction_match:
            qty_expr, unit_part = fraction_match.groups()
            if "/" in qty_expr:
                num, denom = qty_expr.split("/")
                qty_val = float(num.strip()) / float(denom.strip())
            else:
                qty_val = float(qty_expr.strip())

            unit_cleaned = self._clean_text(unit_part).replace(" ", "")
            if unit_cleaned in self.UNIT_MAP:
                base_unit, base_mult = self.UNIT_MAP[unit_cleaned]
                return base_unit, qty_val * base_mult
            if unit_part.strip() in self.UNIT_MAP:
                base_unit, base_mult = self.UNIT_MAP[unit_part.strip()]
                return base_unit, qty_val * base_mult

        raise ValueError(f"Unknown or unsupported unit: '{raw_unit}'")


    def normalize_price(self, raw_price: float, raw_unit: str) -> Tuple[float, str]:
        """
        Convert raw price into standardized price per base metric unit.
        Formula: normalized_price = raw_price / multiplier
        Returns: (normalized_price, base_unit)
        """
        base_unit, multiplier = self.normalize_unit(raw_unit)
        if multiplier <= 0:
            raise ValueError(f"Invalid unit multiplier for '{raw_unit}': {multiplier}")
        normalized_price = round(raw_price / multiplier, 2)
        return normalized_price, base_unit


commodity_normalizer = CommodityNormalizer()
