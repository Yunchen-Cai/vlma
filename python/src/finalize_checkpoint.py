import os
import sys
from pathlib import Path

import torch
from transformers import AutoConfig, AutoProcessor, Qwen2_5_VLForConditionalGeneration

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")


def main() -> None:
    if len(sys.argv) not in {3, 4}:
        raise SystemExit(
            "Usage: python finalize_checkpoint.py CHECKPOINT_DIR OUTPUT_DIR BASE_MODEL_DIR(optional)"
        )

    checkpoint_dir = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    if len(sys.argv) == 4:
        base_model_dir = Path(sys.argv[3]).resolve()
    else:
        base_model_dir = checkpoint_dir.parents[2] / "models" / "Qwen2.5-VL-7B-Instruct"

    print(f"Checkpoint: {checkpoint_dir}")
    print(f"Output: {output_dir}")
    print(f"Base model assets: {base_model_dir}")

    config = AutoConfig.from_pretrained(base_model_dir, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(base_model_dir, trust_remote_code=True)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        checkpoint_dir,
        config=config,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    processor.save_pretrained(output_dir)
    print(f"Saved finalized model to: {output_dir}")


if __name__ == "__main__":
    main()
