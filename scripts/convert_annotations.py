"""
convert_annotations.py
========================
Converte anotações entre formatos populares e o formato YOLO usado neste projeto.

Formatos suportados:
    yolo   → formato nativo (class_id x_c y_c w h  normalizados 0-1)
    coco   → JSON com lista de anotações {bbox: [x,y,w,h], category_id, image_id}
    voc    → XML Pascal-VOC por imagem (xmin ymin xmax ymax)
    csv    → CSV com colunas: filename,class_id,x_center,y_center,width,height
    tfrecord — NÃO implementado (requer tensorflow); mencionado para completude

Uso:
    # YOLO → COCO JSON
    python scripts/convert_annotations.py yolo-to-coco \\
        --labels dataset/train/labels \\
        --images dataset/train/images \\
        --data   dataset/data.yaml    \\
        --output dataset/train/annotations_coco.json

    # COCO JSON → YOLO
    python scripts/convert_annotations.py coco-to-yolo \\
        --coco   dataset/train/annotations_coco.json \\
        --output dataset/train/labels_yolo

    # Pascal-VOC dir → YOLO
    python scripts/convert_annotations.py voc-to-yolo \\
        --voc    /path/to/voc_xmls \\
        --data   dataset/data.yaml \\
        --output dataset/train/labels_yolo

    # YOLO → CSV
    python scripts/convert_annotations.py yolo-to-csv \\
        --labels dataset/train/labels \\
        --output dataset/train/labels.csv

    # CSV → YOLO
    python scripts/convert_annotations.py csv-to-yolo \\
        --csv    dataset/train/labels.csv \\
        --output dataset/train/labels_yolo

    # Validate — check all labels match their images
    python scripts/convert_annotations.py validate \\
        --labels dataset/train/labels \\
        --images dataset/train/images
"""

from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPG", ".JPEG", ".PNG"}


def load_class_names(data_yaml: Path) -> dict[int, str]:
    """Return {class_id: class_name} from a YOLO data.yaml."""
    with open(data_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    names = cfg.get("names", {})
    if isinstance(names, list):
        return {i: n for i, n in enumerate(names)}
    return {int(k): v for k, v in names.items()}


def name_to_id(class_names: dict[int, str]) -> dict[str, int]:
    return {v: k for k, v in class_names.items()}


def read_yolo_file(path: Path) -> list[tuple[int, float, float, float, float]]:
    """Return list of (class_id, x_c, y_c, w, h) normalised."""
    rows = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        rows.append((int(parts[0]), float(parts[1]), float(parts[2]),
                     float(parts[3]), float(parts[4])))
    return rows


def get_image_size(img_path: Path) -> tuple[int, int]:
    """Return (width, height) without loading full image data."""
    from PIL import Image
    with Image.open(img_path) as im:
        return im.size  # (width, height)


def find_image(images_dir: Path, stem: str) -> Path | None:
    for ext in IMAGE_EXTENSIONS:
        p = images_dir / f"{stem}{ext}"
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# YOLO → COCO
# ---------------------------------------------------------------------------

def yolo_to_coco(
    labels_dir: Path,
    images_dir: Path,
    class_names: dict[int, str],
    output: Path,
) -> None:
    coco: dict[str, Any] = {
        "info": {"description": "Converted from YOLO", "version": "1.0"},
        "licenses": [],
        "categories": [{"id": k, "name": v, "supercategory": "architecture"}
                       for k, v in sorted(class_names.items())],
        "images": [],
        "annotations": [],
    }

    ann_id = 1
    img_id = 1

    for lbl_file in sorted(labels_dir.glob("*.txt")):
        stem = lbl_file.stem
        img_path = find_image(images_dir, stem)
        if img_path is None:
            print(f"  [WARN] No image found for label: {lbl_file.name}")
            continue

        w, h = get_image_size(img_path)
        coco["images"].append({
            "id": img_id,
            "file_name": img_path.name,
            "width": w,
            "height": h,
        })

        for cls_id, xc, yc, bw, bh in read_yolo_file(lbl_file):
            x1 = (xc - bw / 2) * w
            y1 = (yc - bh / 2) * h
            bw_px = bw * w
            bh_px = bh * h
            coco["annotations"].append({
                "id": ann_id,
                "image_id": img_id,
                "category_id": cls_id,
                "bbox": [round(x1, 2), round(y1, 2), round(bw_px, 2), round(bh_px, 2)],
                "area": round(bw_px * bh_px, 2),
                "iscrowd": 0,
            })
            ann_id += 1
        img_id += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(coco, f, indent=2, ensure_ascii=False)

    print(f"COCO JSON written → {output}  "
          f"({img_id-1} images, {ann_id-1} annotations)")


# ---------------------------------------------------------------------------
# COCO → YOLO
# ---------------------------------------------------------------------------

def coco_to_yolo(coco_json: Path, output_dir: Path) -> None:
    with open(coco_json, encoding="utf-8") as f:
        data = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    img_map: dict[int, dict[str, Any]] = {img["id"]: img for img in data["images"]}

    # Group annotations by image
    ann_by_img: dict[int, list[dict[str, Any]]] = {}
    for ann in data["annotations"]:
        ann_by_img.setdefault(ann["image_id"], []).append(ann)

    converted = 0
    for img_id, anns in ann_by_img.items():
        img_info = img_map[img_id]
        w, h = img_info["width"], img_info["height"]
        stem = Path(img_info["file_name"]).stem
        lines: list[str] = []
        for ann in anns:
            x1, y1, bw_px, bh_px = ann["bbox"]
            xc = (x1 + bw_px / 2) / w
            yc = (y1 + bh_px / 2) / h
            nw = bw_px / w
            nh = bh_px / h
            cls_id = ann["category_id"]
            lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")
        (output_dir / f"{stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        converted += 1

    print(f"YOLO labels written → {output_dir}  ({converted} files)")


# ---------------------------------------------------------------------------
# Pascal-VOC → YOLO
# ---------------------------------------------------------------------------

def voc_to_yolo(
    voc_dir: Path,
    class_names: dict[int, str],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    n2id = name_to_id(class_names)
    converted = 0
    skipped = 0

    for xml_file in sorted(voc_dir.glob("*.xml")):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        size = root.find("size")
        if size is None:
            print(f"  [WARN] No <size> in {xml_file.name}, skipping")
            skipped += 1
            continue
        w = int(size.findtext("width", "0") or 0)
        h = int(size.findtext("height", "0") or 0)
        if w == 0 or h == 0:
            print(f"  [WARN] Zero size in {xml_file.name}, skipping")
            skipped += 1
            continue

        lines: list[str] = []
        for obj in root.findall("object"):
            name = obj.findtext("name", "").strip()
            if name not in n2id:
                print(f"  [WARN] Unknown class '{name}' in {xml_file.name}")
                continue
            cls_id = n2id[name]
            bndbox = obj.find("bndbox")
            if bndbox is None:
                continue
            xmin = float(bndbox.findtext("xmin", "0") or 0)
            ymin = float(bndbox.findtext("ymin", "0") or 0)
            xmax = float(bndbox.findtext("xmax", "0") or 0)
            ymax = float(bndbox.findtext("ymax", "0") or 0)
            xc = (xmin + xmax) / 2 / w
            yc = (ymin + ymax) / 2 / h
            bw = (xmax - xmin) / w
            bh = (ymax - ymin) / h
            lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

        stem = xml_file.stem
        (output_dir / f"{stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        converted += 1

    print(f"YOLO labels written → {output_dir}  ({converted} converted, {skipped} skipped)")


# ---------------------------------------------------------------------------
# YOLO → CSV
# ---------------------------------------------------------------------------

def yolo_to_csv(labels_dir: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for lbl_file in sorted(labels_dir.glob("*.txt")):
        for cls_id, xc, yc, bw, bh in read_yolo_file(lbl_file):
            rows.append({
                "filename":  lbl_file.stem,
                "class_id":  cls_id,
                "x_center":  xc,
                "y_center":  yc,
                "width":     bw,
                "height":    bh,
            })
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "class_id",
                                               "x_center", "y_center",
                                               "width", "height"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV written → {output}  ({len(rows)} rows)")


# ---------------------------------------------------------------------------
# CSV → YOLO
# ---------------------------------------------------------------------------

def csv_to_yolo(csv_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Group rows by filename
    groups: dict[str, list[str]] = {}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stem = row["filename"]
            line = (f"{row['class_id']} {row['x_center']} "
                    f"{row['y_center']} {row['width']} {row['height']}")
            groups.setdefault(stem, []).append(line)

    for stem, lines in groups.items():
        (output_dir / f"{stem}.txt").write_text("\n".join(lines), encoding="utf-8")

    print(f"YOLO labels written → {output_dir}  ({len(groups)} files)")


# ---------------------------------------------------------------------------
# Validate — check every label has a matching image and vice-versa
# ---------------------------------------------------------------------------

def validate(labels_dir: Path, images_dir: Path) -> None:
    label_stems = {f.stem for f in labels_dir.glob("*.txt")}
    image_stems = {f.stem for f in images_dir.iterdir()
                   if f.suffix.lower() in {e.lower() for e in IMAGE_EXTENSIONS}}

    missing_images = label_stems - image_stems
    missing_labels = image_stems - label_stems

    print(f"Labels : {len(label_stems)}")
    print(f"Images : {len(image_stems)}")

    if missing_images:
        print(f"\n[WARN] {len(missing_images)} labels without matching image:")
        for s in sorted(missing_images)[:20]:
            print(f"  {s}")
    else:
        print("  All labels have a matching image ✓")

    if missing_labels:
        print(f"\n[WARN] {len(missing_labels)} images without matching label:")
        for s in sorted(missing_labels)[:20]:
            print(f"  {s}")
    else:
        print("  All images have a matching label ✓")

    # Check YOLO annotation sanity
    errors = 0
    for lbl_file in labels_dir.glob("*.txt"):
        for i, line in enumerate(lbl_file.read_text(encoding="utf-8").strip().splitlines()):
            parts = line.split()
            if len(parts) < 5:
                print(f"  [ERROR] {lbl_file.name} line {i+1}: expected 5 fields, got {len(parts)}")
                errors += 1
                continue
            try:
                xc, yc, bw, bh = map(float, parts[1:5])
            except ValueError:
                print(f"  [ERROR] {lbl_file.name} line {i+1}: non-numeric values")
                errors += 1
                continue
            if not (0 <= xc <= 1 and 0 <= yc <= 1 and 0 < bw <= 1 and 0 < bh <= 1):
                print(f"  [ERROR] {lbl_file.name} line {i+1}: values out of [0,1] range: "
                      f"xc={xc:.4f} yc={yc:.4f} w={bw:.4f} h={bh:.4f}")
                errors += 1

    if errors == 0:
        print("  All annotation values in valid range ✓")
    else:
        print(f"\n  {errors} annotation errors found.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert annotation formats ↔ YOLO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- yolo-to-coco ---
    p = sub.add_parser("yolo-to-coco", help="YOLO labels → COCO JSON")
    p.add_argument("--labels", required=True, type=Path)
    p.add_argument("--images", required=True, type=Path)
    p.add_argument("--data",   required=True, type=Path, help="data.yaml")
    p.add_argument("--output", required=True, type=Path)

    # --- coco-to-yolo ---
    p = sub.add_parser("coco-to-yolo", help="COCO JSON → YOLO labels")
    p.add_argument("--coco",   required=True, type=Path, help="COCO JSON file")
    p.add_argument("--output", required=True, type=Path, help="Output labels directory")

    # --- voc-to-yolo ---
    p = sub.add_parser("voc-to-yolo", help="Pascal-VOC XMLs → YOLO labels")
    p.add_argument("--voc",    required=True, type=Path, help="Directory with .xml files")
    p.add_argument("--data",   required=True, type=Path, help="data.yaml")
    p.add_argument("--output", required=True, type=Path)

    # --- yolo-to-csv ---
    p = sub.add_parser("yolo-to-csv", help="YOLO labels → CSV")
    p.add_argument("--labels", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path, help="Output .csv file")

    # --- csv-to-yolo ---
    p = sub.add_parser("csv-to-yolo", help="CSV → YOLO labels")
    p.add_argument("--csv",    required=True, type=Path)
    p.add_argument("--output", required=True, type=Path, help="Output labels directory")

    # --- validate ---
    p = sub.add_parser("validate", help="Validate label↔image consistency")
    p.add_argument("--labels", required=True, type=Path)
    p.add_argument("--images", required=True, type=Path)

    args = parser.parse_args()

    if args.command == "yolo-to-coco":
        class_names = load_class_names(args.data)
        yolo_to_coco(args.labels, args.images, class_names, args.output)

    elif args.command == "coco-to-yolo":
        coco_to_yolo(args.coco, args.output)

    elif args.command == "voc-to-yolo":
        class_names = load_class_names(args.data)
        voc_to_yolo(args.voc, class_names, args.output)

    elif args.command == "yolo-to-csv":
        yolo_to_csv(args.labels, args.output)

    elif args.command == "csv-to-yolo":
        csv_to_yolo(args.csv, args.output)

    elif args.command == "validate":
        validate(args.labels, args.images)


if __name__ == "__main__":
    main()
