import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Merge multiple JSON SFT datasets into one file.")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input JSON files.")
    parser.add_argument("--output", required=True, help="Output merged JSON file.")
    return parser.parse_args()


def main():
    args = parse_args()
    merged = []
    for path_str in args.inputs:
        path = Path(path_str)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Expected list in {path}")
        merged.extend(data)
        print(f"loaded {len(data)} from {path}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"wrote {len(merged)} samples to {output}")


if __name__ == "__main__":
    main()
