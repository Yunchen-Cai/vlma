import argparse
import csv
from pathlib import Path

import cv2


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LABEL_BY_FOLDER = {
    "finish": ("Finish", "Finish"),
    "unfinish": ("Unfinish", "Unfinish"),
    "clearly_unfinish": ("Unfinish", "Clearly_Unfinish"),
    "near_finished_unfinish": ("Unfinish", "Near_Finished_Unfinish"),
}
CSV_FIELDS = [
    "image_path",
    "part",
    "gt_verification",
    "hard_case",
    "x1",
    "y1",
    "x2",
    "y2",
    "roi_type",
    "notes",
]

KEY_ENTER = {13, 10}
KEY_SPACE = 32
KEY_ESCAPE = 27
KEY_Q = ord("q")
KEY_R = ord("r")
KEY_S = ord("s")
KEY_H = ord("h")
KEY_MINUS = ord("-")
KEY_EQUALS = ord("=")
KEY_PLUS = ord("+")


class BoxEditor:
    def __init__(self, image, box=None):
        self.image = image
        self.box = box
        self.start = None

    def on_mouse(self, event, x, y, flags, _parameter):
        height, width = self.image.shape[:2]
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start = (x, y)
            self.box = (x, y, x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self.start is not None:
            x0, y0 = self.start
            self.box = clamp_box(
                (min(x0, x), min(y0, y), max(x0, x), max(y0, y)),
                width,
                height,
            )
        elif event == cv2.EVENT_LBUTTONUP:
            if self.start is not None:
                x0, y0 = self.start
                self.box = clamp_box(
                    (min(x0, x), min(y0, y), max(x0, x), max(y0, y)),
                    width,
                    height,
                )
            self.start = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Interactively annotate one ROI bounding box per assembly image."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Folder containing Finish/Unfinish, or the three hard-case folders.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        required=True,
        help="Metadata CSV to create or resume.",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
        help="Paths in output CSV are stored relative to this directory when possible.",
    )
    parser.add_argument("--part", default="Port End Cover")
    parser.add_argument(
        "--preview-root",
        type=Path,
        help="Optional directory for images with the saved bounding box drawn on them.",
    )
    parser.add_argument(
        "--reannotate-missing-previews",
        action="store_true",
        help="Only review existing annotations whose preview image has been deleted.",
    )
    return parser.parse_args()


def find_images(input_root):
    images = []
    folder_lookup = {path.name.lower(): path for path in input_root.iterdir() if path.is_dir()}
    supported_folders = [
        folder_lookup[name]
        for name in LABEL_BY_FOLDER
        if name in folder_lookup
    ]
    if not supported_folders:
        raise FileNotFoundError(
            f"No supported category folders found under {input_root}. "
            f"Expected one or more of: {', '.join(LABEL_BY_FOLDER)}"
        )
    for folder in supported_folders:
        images.extend(
            sorted(
                path
                for path in folder.rglob("*")
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
            )
        )
    return images


def read_existing(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return {row["image_path"]: row for row in csv.DictReader(file)}


def relative_image_path(path, data_root):
    try:
        return path.resolve().relative_to(data_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows.values())


def folder_labels(image_path):
    folder_key = image_path.parent.name.lower()
    if folder_key not in LABEL_BY_FOLDER:
        raise ValueError(f"Unsupported category folder: {image_path.parent.name}")
    return LABEL_BY_FOLDER[folder_key]


def save_preview(image, box, image_path, preview_root, input_root):
    if preview_root is None:
        return
    preview = image.copy()
    x1, y1, x2, y2 = box
    cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 3)
    relative = image_path.relative_to(input_root)
    output_path = preview_root / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), preview)


def preview_path_for(image_path, preview_root, input_root):
    if preview_root is None:
        return None
    return preview_root / image_path.relative_to(input_root)


def box_from_row(row):
    return tuple(int(row[key]) for key in ("x1", "y1", "x2", "y2"))


def draw_overlay(image, box, position, total, category):
    display = image.copy()
    if box is not None:
        x1, y1, x2, y2 = box
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 3)
    cv2.putText(
        display,
        f"{position}/{total} | {category} | Enter save | R redraw | Arrows move | +/- resize | S skip | Q quit",
        (15, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return display


def clamp_box(box, width, height):
    x1, y1, x2, y2 = box
    x1 = max(0, min(width - 1, x1))
    y1 = max(0, min(height - 1, y1))
    x2 = max(1, min(width, x2))
    y2 = max(1, min(height, y2))
    if x2 <= x1:
        x2 = min(width, x1 + 1)
    if y2 <= y1:
        y2 = min(height, y1 + 1)
    return x1, y1, x2, y2


def move_box(box, dx, dy, width, height):
    x1, y1, x2, y2 = box
    box_width = x2 - x1
    box_height = y2 - y1
    x1 = max(0, min(width - box_width, x1 + dx))
    y1 = max(0, min(height - box_height, y1 + dy))
    return x1, y1, x1 + box_width, y1 + box_height


def resize_box(box, delta, width, height):
    x1, y1, x2, y2 = box
    return clamp_box((x1 - delta, y1 - delta, x2 + delta, y2 + delta), width, height)


def review_or_redraw_box(window_name, image, default_box, position, total, category):
    editor = BoxEditor(image, default_box)
    height, width = image.shape[:2]
    step = max(2, round(min(width, height) * 0.01))
    cv2.setMouseCallback(window_name, editor.on_mouse)
    while True:
        cv2.imshow(
            window_name,
            draw_overlay(image, editor.box, position, total, category),
        )
        key = cv2.waitKeyEx(20)
        if key == -1:
            continue
        if key in KEY_ENTER or key == KEY_SPACE:
            if editor.box is not None:
                return editor.box, "save"
            print("Draw a rectangle before saving.")
            continue
        if key in {KEY_Q, KEY_ESCAPE}:
            return editor.box, "quit"
        if key == KEY_S:
            return editor.box, "skip"
        if key == KEY_R:
            editor.box = None
            continue
        if key == KEY_H:
            print(
                "Mouse: drag with left button to draw a rectangle. "
                "Keys: Enter save, R clear, arrows move, +/- resize, S skip, Q/Esc quit"
            )
            continue
        if key == KEY_MINUS:
            if editor.box is not None:
                editor.box = resize_box(editor.box, -step, width, height)
            continue
        if key in {KEY_EQUALS, KEY_PLUS}:
            if editor.box is not None:
                editor.box = resize_box(editor.box, step, width, height)
            continue
        if key == 2424832:  # Left
            if editor.box is not None:
                editor.box = move_box(editor.box, -step, 0, width, height)
            continue
        if key == 2555904:  # Right
            if editor.box is not None:
                editor.box = move_box(editor.box, step, 0, width, height)
            continue
        if key == 2490368:  # Up
            if editor.box is not None:
                editor.box = move_box(editor.box, 0, -step, width, height)
            continue
        if key == 2621440:  # Down
            if editor.box is not None:
                editor.box = move_box(editor.box, 0, step, width, height)
            continue


def annotate(args):
    images = find_images(args.input_root)
    existing = read_existing(args.output_csv)
    if args.reannotate_missing_previews:
        if args.preview_root is None:
            raise ValueError("--reannotate-missing-previews requires --preview-root.")
        pending = [
            image
            for image in images
            if relative_image_path(image, args.data_root) in existing
            and not preview_path_for(image, args.preview_root, args.input_root).exists()
        ]
        mode = "missing-preview annotations to review"
    else:
        pending = [
            image
            for image in images
            if relative_image_path(image, args.data_root) not in existing
        ]
        mode = "pending annotations"

    print(
        f"Found {len(images)} images; {len(existing)} annotated; "
        f"{len(pending)} {mode}."
    )
    print("Mouse: hold left button and drag to draw/redraw a rectangle.")
    print("Next images inherit the previous ROI: ENTER saves, R clears, arrows move, +/- resize, S skips, Q exits.")

    window_name = "ROI Annotation"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    last_box = None

    try:
        index = 0
        while index < len(pending):
            image_path = pending[index]
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"Skipping unreadable image: {image_path}")
                index += 1
                continue

            verification, hard_case = folder_labels(image_path)
            image_key = relative_image_path(image_path, args.data_root)
            default_box = (
                box_from_row(existing[image_key])
                if args.reannotate_missing_previews
                else last_box
            )
            box, action = review_or_redraw_box(
                window_name,
                image,
                default_box,
                index + 1,
                len(pending),
                image_path.parent.name,
            )

            if action == "quit":
                break
            if action == "skip":
                index += 1
                continue
            if box is None:
                continue

            x1, y1, x2, y2 = box
            existing[image_key] = {
                "image_path": image_key,
                "part": args.part,
                "gt_verification": verification,
                "hard_case": hard_case,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "roi_type": "bbox",
                "notes": "",
            }
            write_rows(args.output_csv, existing)
            save_preview(
                image, box, image_path, args.preview_root, args.input_root
            )
            last_box = box
            index += 1
    finally:
        write_rows(args.output_csv, existing)
        cv2.destroyAllWindows()

    print(f"Saved {len(existing)} annotations to {args.output_csv}")


def main():
    annotate(parse_args())


if __name__ == "__main__":
    main()
