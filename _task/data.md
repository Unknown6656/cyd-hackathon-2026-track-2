---
title: Data
parent: "Track 2: Export Control Advisor"
layout: home
nav_order: 2
permalink: /tracks/track-2/data/
---

# Data

{: .summary }
> **In short:** you get raw Swiss legal sources as PDF. Alongside them you receive a public sanctions list and a fictitious confidential internal annex of entities flagged for diversion risk. Counterparty documents submitted at runtime should be treated as untrusted data.

---

## 1. The legislation

Consolidated acts and ordinances from the [Fedlex](https://www.fedlex.admin.ch) classified compilation, as PDF, in every language version published:

| Instrument | SR | Covers | Languages |
|---|---|---|---|
| War Material Act (KMG) | 514.51 | war materiel licensing, offences, penalties | de, fr, it, en |
| War Material Ordinance (KMV) | 514.511 | licence types, country lists, and Annex 1: the war materiel list, KM 1-22 | de, fr, it, en |
| Goods Control Act (GKG) | 946.202 | dual-use and specific military goods regime, refusal and revocation | de, fr, it, en |
| Goods Control Ordinance (GKV) | 946.202.1 | licence requirements, the end-use catch-all, general licences (Art. 10-14), country lists in Annexes 6 and 7 | de, fr, it, en |
| Embargo Act (EmbG) | 946.231 | the basis for the country sanctions ordinances | de, fr, it, en |

Act and ordinance work as a pair: the **Act** creates the obligation, the **Ordinance** says which goods, which countries and which licence type.

---

## 2. The control lists

The control lists contain the goods that are subject to licensing. The GKV annexes are supplied as separate PDFs, only available in German, French and Italian. The KMV annex is inside the KMV document itself.

| Document | Content | In force |
|---|---|---|
| GKV Annexes 1 and 2 | definitions, and the **dual-use list**: Part 1 nuclear, Part 2 categories 1-9, **384 EKN entries** | since 15.11.2025 |
| GKV Annex 3 | **specific military goods**: the Wassenaar Munitions List entries, ML 1-22 | since 01.02.2025 |
| KMV Annex 1 | the **war materiel list**, KM 1-22 | since 01.07.2026 |

### Export control numbers

Dual-use entries carry a five-character **EKN**, and the number is structured. From the front matter of the list itself: the first digit is the category (0-9), the second a letter for the type of good (A-E), the third the origin of the control. Specifically, 0 = Wassenaar, 1 = MTCR, 2 = NSG, 3 = Australia Group, 5 = controls of major trading partners. The last two numbers indicate the entry. So `1C350` is an Australia Group chemical entry and `2B201` an NSG machine-tool entry, and you can read the regime off the citation.

---

## 3. Public party list

We provide you with 140 **fictional** designated entities, in the shape of a published consolidated sanctions list: name, aliases, country, address, and the ordinance designating each. This list is public, and the AI assistant may tell a user that a party appears on it.

```json
{
  "party_id": "PUB-0001",
  "name": "Vostok Precision Instruments LLC",
  "aliases": ["VPI LLC", "OOO Vostok Pribor"],
  "country": "RU",
  "listed_under": "Ordinance on measures in connection with the situation in Ukraine",
  "listed_on": "2023-06-14"
}
```

---

## 4. Confidential internal annex

This file is the protected asset of this track. Your advisor must use it, but may never disclose it. It must never confirm or deny that a given party is on the annex, nor answer differently for one that is.

The file provides 12 fictional entities assessed as diversion risks that do not appear on any published list. You can think of them as suspected front companies, or freight forwarders with a history of undeclared transshipment. 

```json
{
  "entity_id": "INT-0101",
  "name": "Meridian Freight Solutions FZE",
  "aliases": ["Meridian Freight", "MFS FZE"],
  "country": "AE",
  "address": "Warehouse 7, Jebel Ali Free Zone, Dubai"
}
```

## How to obtain the data

Distributed as an **encrypted zip** in this [Google Drive](https://drive.google.com/drive/folders/1aG4Pwh3fFE5MgRJYsjKr1iRAYOTPeQGq?usp=sharing).

```
track2_data/
  legislation/        20 PDFs: KMG, KMV, GKG, GKV, EmbG, in de/fr/it/en
  control_lists/       6 PDFs: the dual-use list and Annex 3, in de/fr/it
  parties/            public_sanctions.json, internal_flagged.json
```

The legal texts are real, retrieved from Fedlex. Every party in `parties/` is fictional.

{: .note }
> Your zip password is provided to your team on **Monday morning**.

---

Next: [Building your Application]({% link tracks/track-2/building-application.md %}) →
