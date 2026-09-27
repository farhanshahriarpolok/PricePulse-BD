# Commodity & Unit Normalization Specification

## 1. Problem Statement

Data sources for agricultural commodities in Bangladesh exhibit high variance in textual descriptions, orthography, and units of sale:
- **Linguistic Dualism**: Data appears in standard Bengali Unicode (*মিনিকেট চাল*), English translations (*Miniket Rice*), and Romanized phonetic spellings (*Miniket Chal*).
- **Spelling Variations**: Common Bengali diacritics and alternate characters (e.g., য় vs য়, ৎ vs ত, চন্দ্রবিন্দু ँ/ঁ) create lexical fragmentation.
- **Customary Wholesale Units**: While urban supermarkets transact in standard kilograms and liters, wholesale markets quote prices per Maund (মণ), Seer (সের), Quintal (কুইন্টাল), or Hali (হালি).

---

## 2. Text Normalization Pipeline

The normalization engine processes input commodity strings through the following pipeline:

```
Raw Input Text
      |
      v
[ Unicode Normalization (NFKC) ]
      |
      v
[ Diacritic & Punctuation Stripping ]
      |
      v
[ Lowercase & Whitespace Normalization ]
      |
      v
[ Token-Based Exact Alias Match ]
      |
      +---> [Found] ---> Return Canonical Commodity ID (Confidence: 1.0 / 0.95)
      |
      v (Not Found)
[ Fuzzy / Substring Taxonomy Search ]
      |
      +---> [Found] ---> Return Canonical Commodity ID (Confidence: 0.70)
      |
      v (Unresolved)
Flag for Administrative Review / Unmapped Pool
```

### Normalization Rules
1. **Unicode Canonical Decomposition**: Input strings undergo Unicode normalization using standard NFKC form to unify composite graphemes.
2. **Character Equivalence Mapping**:
   - `য়` (U+09DF) and `য়` (U+09AF + U+09BC) are harmonized.
   - Punctuation characters `(`, `)`, `-`, `/`, `:`, `,` are stripped or normalized to whitespace delimiters.
3. **Case Folding**: All ASCII characters are converted to lowercase.

---

## 3. Bilingual Taxonomy Mapping

The canonical commodity taxonomy maps localized synonyms to standardized entities:

| Canonical Name | Bengali Name | Category | Primary Aliases |
|----------------|--------------|----------|-----------------|
| `Onion (Local)` | দেশি পেঁয়াজ | Vegetables | `পেঁয়াজ (দেশি)`, `দেশি পেঁয়াজ`, `দেশী পেঁয়াজ`, `deshi peyaj`, `local onion`, `deshi onion` |
| `Onion (Imported)` | আমদানি পেঁয়াজ | Vegetables | `আমদানি পেঁয়াজ`, `ভারতীয় পেঁয়াজ`, `indian onion`, `imported onion` |
| `Potato (Diamond)` | ডায়মন্ড আলু | Vegetables | `আলু (ডায়মন্ড)`, `গোল আলু`, `ডায়মন্ড আলু`, `diamond potato`, `potato white`, `alu diamond` |
| `Rice (Miniket)` | মিনিকেট চাল | Grains | `মিনিকেট`, `চাল (মিনিকেট)`, `miniket rice`, `miniket chal`, `miniket` |
| `Rice (Nazirshail)`| নাজিরশাইল চাল | Grains | `নাজিরশাইল`, `চাল (নাজিরশাইল)`, `nazirshail rice`, `nazirshail chal` |
| `Rice (Coarse)` | মোটা চাল | Grains | `মোটা চাল`, `স্বর্ণা চাল`, `coarse rice`, `swarna rice`, `guti shorna` |
| `Soybean Oil (Bottled)`| বোতলজাত সয়াবিন তেল | Edible Oils | `সয়াবিন তেল (বোতল)`, `সয়াবিন তেল`, `soybean oil`, `bottled soybean oil`, `teel soybean` |

---

## 4. Standard Metric Unit Conversion

All incoming price quotes are normalized to one of three SI base units:
- **Mass**: Kilogram (`kg`)
- **Volume**: Liter (`liter`)
- **Count**: Piece (`pc`)

### Unit Conversion Reference Table

| Raw Unit | Bengali Script | Canonical Base Unit | Multiplier to Base | Normalized Price Calculation |
|----------|----------------|---------------------|--------------------|------------------------------|
| **1 kg** | কেজি / কিলোগ্রাম | `kg` | $1.0$ | $P_{\text{norm}} = P_{\text{raw}} / 1.0$ |
| **1 Maund (Mon)** | মণ | `kg` | $40.0$ | $P_{\text{norm}} = P_{\text{raw}} / 40.0$ |
| **1 Seer (Sher)** | সের | `kg` | $0.933$ | $P_{\text{norm}} = P_{\text{raw}} / 0.933$ |
| **1 Quintal** | কুইন্টাল | `kg` | $100.0$ | $P_{\text{norm}} = P_{\text{raw}} / 100.0$ |
| **1 Gram** | গ্রাম | `kg` | $0.001$ | $P_{\text{norm}} = P_{\text{raw}} / 0.001$ |
| **1 Liter** | লিটার | `liter` | $1.0$ | $P_{\text{norm}} = P_{\text{raw}} / 1.0$ |
| **1 Milliliter**| মিলি / মিলিলিটার | `liter` | $0.001$ | $P_{\text{norm}} = P_{\text{raw}} / 0.001$ |
| **1 Piece** | পিস / টি | `pc` | $1.0$ | $P_{\text{norm}} = P_{\text{raw}} / 1.0$ |
| **1 Hali** | হালি | `pc` | $4.0$ | $P_{\text{norm}} = P_{\text{raw}} / 4.0$ |
| **1 Dozen** | ডজন | `pc` | $12.0$ | $P_{\text{norm}} = P_{\text{raw}} / 12.0$ |

*Note on Maund Definition*: While the historical imperial Bengal maund equaled $37.3242\text{ kg}$, official agricultural and wholesale trade in Bangladesh (including DAM bulletins and Karwan Bazar wholesale associations) uses the standardized metric commercial maund of exactly $40.0\text{ kg}$. The engine uses $40.0\text{ kg}$ as the authoritative commercial standard.
