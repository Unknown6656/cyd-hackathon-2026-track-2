---
title: Introduction
parent: "Track 2: Export Control Advisor"
nav_order: 1
layout: home
permalink: /tracks/track-2/introduction/
---

# Introduction

{: .summary }
> **In short:** build a compliance advisor over Swiss arms and dual-use export control law. It must tell an exporter which regime a product falls under, whether a shipment needs a licence, and whether the counterparty is a diversion risk. The response must be grounded in cited provisions, never disclose the confidential list of flagged entities, and never help anyone engineer their way around a control.

## Scenario

A Swiss optronics manufacturer builds thermal imaging and sighting systems. The same detector core runs through most of the product line, and where it ends up decides which law applies. On the one hand, war materiel is licensed by the Confederation under the [War Material Act](https://www.fedlex.admin.ch/eli/cc/1998/794_794_794/en). On the other hand, industrial and civil thermal cameras are dual-use goods licensed under the [Goods Control Act](https://www.fedlex.admin.ch/eli/cc/1997/1697_1697_1697/en). 

The company has a small compliance desk that must clear every outgoing order, and is looking to leverage an AI assistant to help them answer the questions that come up every week.

## Task

Build an assistant that, grounded in the provided legal corpus and party lists:

- **classifies** an item against the control lists, returning the specific entry it falls under, in the war materiel list or the dual-use list, and the text that decides it.
- **assesses** a proposed transaction and returns a licensing verdict, the provisions that trigger it, and any diversion red flags,
- **answers** free-text compliance questions with article-level citations

It has to do all of this without ever disclosing the confidential internal list of flagged entities.

---

Next: [Data]({% link tracks/track-2/data.md %}) →
