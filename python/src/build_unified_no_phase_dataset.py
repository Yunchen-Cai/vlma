import argparse
import json
import re
from pathlib import Path


GENERAL_PROMPT = (
    'You are an assembly quality inspector. Observe this frame. '
    'Identify the hand action, tool, and part.\n\n'
    'Allowed Parts: ["Mounting Flange", "Gear Housing", "Thrust Block", '
    '"Drive Gear", "Driven Gear", "Port End Cover", "Capscrew"]\n\n'
    'Output ONLY in this JSON format: {"action": "...", "tool": "...", "part": "..."}'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build unified no-phase ATP/verification datasets."
    )
    parser.add_argument("--general-train", required=True)
    parser.add_argument("--general-eval", required=True)
    parser.add_argument("--verification-full", required=True)
    parser.add_argument("--verification-mixed", required=True)
    parser.add_argument("--output-root", required=True)
    return parser.parse_args()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_general_prompt(text: str) -> str:
    if not text:
        return GENERAL_PROMPT
    text = re.sub(
        r"Identify the hand action, tool, part, and phase\.",
        "Identify the hand action, tool, and part.",
        text,
    )
    text = re.sub(
        r'Output ONLY in this JSON format:\s*\{"action": "\.\.\.", "tool": "\.\.\.", "part": "\.\.\.", "phase": "\.\.\."\}',
        'Output ONLY in this JSON format: {"action": "...", "tool": "...", "part": "..."}',
        text,
    )
    return text


def strip_phase_from_general_item(item: dict) -> dict:
    output = {
        "image": item["image"],
        "messages": [],
    }
    messages = item.get("messages", item.get("conversations"))
    if not messages:
        raise ValueError("Missing messages/conversations")
    for idx, message in enumerate(messages):
        msg = {"role": message["role"], "content": message["content"]}
        if idx == 0 and isinstance(message["content"], list):
            new_content = []
            for entry in message["content"]:
                if entry.get("type") == "text":
                    new_entry = dict(entry)
                    new_entry["text"] = normalize_general_prompt(entry.get("text", ""))
                    new_content.append(new_entry)
                else:
                    new_content.append(entry)
            msg["content"] = new_content
        elif idx == len(messages) - 1 and isinstance(message["content"], str):
            gt = json.loads(message["content"])
            msg["content"] = json.dumps(
                {
                    "action": gt.get("action", ""),
                    "tool": gt.get("tool", ""),
                    "part": gt.get("part", ""),
                },
                ensure_ascii=False,
            )
        output["messages"].append(msg)
    return output


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root)

    general_train = [strip_phase_from_general_item(item) for item in load_json(Path(args.general_train))]
    general_eval = [strip_phase_from_general_item(item) for item in load_json(Path(args.general_eval))]
    verification_full = load_json(Path(args.verification_full))
    verification_mixed = load_json(Path(args.verification_mixed))

    general_only_train_path = output_root / "sft" / "general_atp_only_sft_v1.json"
    general_eval_path = output_root / "eval" / "general_atp_only_eval_v1.json"
    atp_plus_full_path = output_root / "sft" / "general_plus_verification_full_sft_v1.json"
    atp_plus_mixed_path = output_root / "sft" / "general_plus_verification_full_roi_mixed_sft_v1.json"

    save_json(general_only_train_path, general_train)
    save_json(general_eval_path, general_eval)
    save_json(atp_plus_full_path, general_train + verification_full)
    save_json(atp_plus_mixed_path, general_train + verification_mixed)

    metadata = {
        "general_train_samples": len(general_train),
        "general_eval_samples": len(general_eval),
        "verification_full_samples": len(verification_full),
        "verification_mixed_samples": len(verification_mixed),
        "outputs": {
            "general_atp_only_sft_v1": str(general_only_train_path),
            "general_atp_only_eval_v1": str(general_eval_path),
            "general_plus_verification_full_sft_v1": str(atp_plus_full_path),
            "general_plus_verification_full_roi_mixed_sft_v1": str(atp_plus_mixed_path),
        },
    }
    save_json(output_root / "metadata.json", metadata)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
