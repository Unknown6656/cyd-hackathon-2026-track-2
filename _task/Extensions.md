---
title: Extensions
parent: "Track 2: Export Control Advisor"
nav_order: 6
layout: home
permalink: /tracks/track-2/extensions/
---

# Extensions

{: .summary }
> **Optional.** Once your core advisor works, these are directions to take it further. They are pointers, not requirements: pick any, all, or none, and feel free to go your own way.

Your baseline is the advisor from [Building your Application]({% link tracks/track-2/building-application.md %}). Everything here is on top of that.

---

## 1. Add a user interface

Your advisor is an HTTP endpoint, which is enough for grading but not much to look at. A compliance officer would rather see a form and a verdict card than a JSON blob.

{: .tip }
> [Open WebUI](https://openwebui.com) is an open-source chat interface you can point at your advisor. It speaks the OpenAI chat format, so you will likely add a thin adapter between it and your `/advise` endpoint. A case view showing the verdict and the triggering provisions side by side demos far better than a transcript.

---

## 2. Confidence

The contract has no confidence field. Add one: a `confidence` between 0 and 1 in each response block, saying how well-supported that answer is. You can try different approaches here, for example by using the LLM itself, or a separate judge LLM. To assess the scoring, you can compose a small list of transactions for which you know the answer, and see how well your confidence tracks the correctness of the answer. 

---

## 3. Batch triage

Compliance desks do not get one case at a time, they get an order book. Accept a batch of transactions or items and return them ranked by how much human attention each needs. For this, you will need to adjust the request and response formats, and to define a scoring function. 

---


