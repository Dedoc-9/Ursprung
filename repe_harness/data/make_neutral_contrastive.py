#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""make_neutral_contrastive.py — generate a larger NEUTRAL contrastive dataset (cooking=1 vs math=0).

NEUTRAL BY DESIGN: an apparatus/demo dataset for measuring a real *probe AUROC* on your model. It is NOT a
safety dataset — a high AUROC here says nothing about safety (`AUROC != safety`). For a safety number, supply
real harmful/benign text with the same schema and feed it to the same `--extract` path, then Phase 4 on held-out
attacks with `neutral_ruler_ok`.

Usage:
  python make_neutral_contrastive.py [--n 240] [--seed 0] [--out neutral_contrastive.jsonl]
  python ../ingest_activations.py --extract --model Qwen/Qwen2.5-1.5B-Instruct \
         --data data/neutral_contrastive.jsonl --layers 6,12,18 --device auto
"""
import argparse
import json
import os
import random
import re

_V = {
    "veg": ["onions", "garlic", "peppers", "mushrooms", "leeks", "shallots", "spinach", "carrots"],
    "spice": ["cumin", "paprika", "thyme", "chili flakes", "black pepper", "oregano", "ginger"],
    "liquid": ["a splash of milk", "white wine", "chicken stock", "cream", "olive oil", "lemon juice"],
    "pan": ["skillet", "pan", "wok", "saucepan"],
    "dough": ["bread dough", "pizza dough", "pastry", "batter"],
    "sauce": ["tomato sauce", "gravy", "curry", "broth", "reduction"],
    "fruit": ["blueberries", "sliced apples", "raspberries", "diced peaches"],
    "meat": ["chicken", "steak", "salmon", "tofu", "pork"],
    "t": ["an", "a half", "one", "two"],
}
COOK = [
    "Saute the {veg} until golden, then stir in {spice} and a pinch of salt.",
    "Whisk the eggs with {liquid} before pouring them into the hot {pan}.",
    "Let the {dough} rise for {t} hour until it doubles in size.",
    "Simmer the {sauce} on low heat, stirring so it does not catch.",
    "Fold the {fruit} gently into the batter to keep it airy.",
    "Roast the {veg} with {spice} until the edges caramelize.",
    "Season the {meat} and sear it in a hot {pan} for a crust.",
    "Deglaze the {pan} with {liquid} and scrape up the browned bits.",
    "Toss the {veg} in {liquid}, then grill until lightly charred.",
    "Braise the {meat} in {sauce} until it is tender enough to shred.",
]
_M = {
    "fn": ["sin(x)", "cos(x)", "e^x", "ln(x)", "x^2", "x^3", "tan(x)", "1/x"],
    "res": ["zero", "one", "a constant", "1/2", "the same value"],
    "poly": ["x^2 - 5x + 6", "x^2 - 9", "2x^2 + 7x + 3", "x^2 + x - 12"],
    "a": ["3", "5", "7", "2", "11"], "b": ["4", "6", "1", "9", "8"], "c": ["10", "12", "20", "15"],
}
MATH = [
    "The derivative of {fn} with respect to x follows from the chain rule.",
    "Solve for x: {a}x + {b} = {c}, then verify the root by substitution.",
    "The integral of {fn} gives the area under the curve on the interval.",
    "By induction, the statement holds for every natural number n.",
    "A square matrix is invertible if and only if its determinant is nonzero.",
    "The limit of the sequence converges to {res} as n grows without bound.",
    "Factor the polynomial {poly} into its linear terms.",
    "The probability of the event equals {a} divided by {c}.",
    "Differentiate {fn} and set it equal to {res} to find the critical point.",
    "The eigenvalues solve the characteristic polynomial of the matrix.",
]


def _fill(t, vocab, rng):
    return re.sub(r"\{(\w+)\}", lambda m: rng.choice(vocab[m.group(1)]), t)


def generate(n, seed=0):
    rng = random.Random(seed)
    rows = []
    for _ in range(n // 2):
        rows.append({"text": _fill(rng.choice(COOK), _V, rng), "label": 1})
        rows.append({"text": _fill(rng.choice(MATH), _M, rng), "label": 0})
    rng.shuffle(rows)
    return rows


def main():
    ap = argparse.ArgumentParser(description="generate a NEUTRAL cooking-vs-math contrastive set (demo, not safety)")
    ap.add_argument("--n", type=int, default=240)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "neutral_contrastive.jsonl"))
    a = ap.parse_args()
    rows = generate(a.n, a.seed)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    n1 = sum(r["label"] for r in rows)
    print(f"wrote {len(rows)} rows ({n1} cooking / {len(rows) - n1} math) -> {a.out}")
    print("NEUTRAL demo set: yields a real probe AUROC, NOT a safety result. AUROC != safety.")


if __name__ == "__main__":
    main()
