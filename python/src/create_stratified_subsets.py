import json
import random
import sys
from collections import defaultdict
from pathlib import Path


def get_label(item):
    conversations = item.get("conversations", item.get("messages"))
    answer = conversations[-1]["content"]
    payload = json.loads(answer)
    return payload.get("verification", "UNKNOWN")


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit(
            "Usage: python create_stratified_subsets.py INPUT_JSON OUTPUT_DIR SIZE1 [SIZE2 ...]"
        )

    input_json = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    sizes = [int(x) for x in sys.argv[3:]]

    data = json.loads(input_json.read_text(encoding="utf-8"))
    by_label = defaultdict(list)
    for item in data:
        by_label[get_label(item)].append(item)

    rng = random.Random(42)
    for items in by_label.values():
        rng.shuffle(items)

    total = len(data)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input: {input_json}")
    print(f"Total samples: {total}")
    print("Label counts:")
    for label, items in sorted(by_label.items()):
        print(f"  {label}: {len(items)}")

    for size in sizes:
        if size > total:
            raise ValueError(f"Requested subset {size} exceeds total {total}")

        subset = []
        assigned = 0
        labels = sorted(by_label)
        quotas = {}
        for label in labels:
            raw = size * len(by_label[label]) / total
            quotas[label] = int(raw)
            assigned += quotas[label]

        remainders = sorted(
            ((size * len(by_label[label]) / total - quotas[label], label) for label in labels),
            reverse=True,
        )
        for _, label in remainders[: size - assigned]:
            quotas[label] += 1

        for label in labels:
            subset.extend(by_label[label][: quotas[label]])

        rng.shuffle(subset)
        out_path = output_dir / f"{input_json.stem}_{size}.json"
        out_path.write_text(json.dumps(subset, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved {len(subset)} -> {out_path}")


if __name__ == "__main__":
    main()
