"""
verify_dataset.py
=================
Valida a consistência do dataset YOLO antes do treinamento.

Verificações realizadas:
  1. Toda imagem tem um label correspondente (mesmo stem, extensão .txt)
  2. Todo label tem uma imagem correspondente
  3. Cada linha de label tem exatamente 5 campos
  4. Coordenadas normalizadas estão dentro do intervalo [0, 1]
  5. class_id está dentro do range definido em data.yaml
  6. Nenhum label está completamente vazio (imagem sem anotações)
  7. Contagem de imagens por split e distribuição de classes

Uso (a partir da raiz do repositório):

    python scripts/verify_dataset.py
    python scripts/verify_dataset.py --data dataset/data.yaml
    python scripts/verify_dataset.py --data dataset/data.yaml --splits train val
    python scripts/verify_dataset.py --strict   # retorna exit code 1 se houver erros
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_YAML = REPO_ROOT / "dataset" / "data.yaml"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp",
                    ".JPG", ".JPEG", ".PNG", ".BMP", ".WEBP"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_data_yaml(path: Path) -> tuple[Path, dict[int, str]]:
    """Return (dataset_root, {class_id: class_name}) from data.yaml."""
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    raw_path = cfg.get("path", ".")
    # Resolve relative to the yaml file itself (Ultralytics convention)
    dataset_root = (path.parent / raw_path).resolve()

    names = cfg.get("names", {})
    if isinstance(names, list):
        class_names = {i: n for i, n in enumerate(names)}
    else:
        class_names = {int(k): v for k, v in names.items()}

    return dataset_root, class_names


def image_stems(images_dir: Path) -> set[str]:
    return {p.stem for p in images_dir.iterdir()
            if p.suffix in IMAGE_EXTENSIONS}


def label_stems(labels_dir: Path) -> set[str]:
    return {p.stem for p in labels_dir.glob("*.txt")}


# ---------------------------------------------------------------------------
# Per-split verification
# ---------------------------------------------------------------------------

def verify_split(
    split: str,
    dataset_root: Path,
    class_names: dict[int, str],
    errors: list[str],
    warnings: list[str],
) -> Counter:
    """
    Verifica um split (train / val / test).
    Retorna Counter com a distribuição de classes encontrada.
    """
    images_dir = dataset_root / split / "images"
    labels_dir = dataset_root / split / "labels"

    print(f"\n{'─'*55}")
    print(f"  Split: {split}")
    print(f"{'─'*55}")

    # --- Directories must exist ---
    if not images_dir.is_dir():
        errors.append(f"[{split}] Diretório não encontrado: {images_dir}")
        return Counter()
    if not labels_dir.is_dir():
        errors.append(f"[{split}] Diretório não encontrado: {labels_dir}")
        return Counter()

    img_stems = image_stems(images_dir)
    lbl_stems = label_stems(labels_dir)

    n_images = len(img_stems)
    n_labels = len(lbl_stems)
    print(f"  Imagens : {n_images}")
    print(f"  Labels  : {n_labels}")

    # --- Check 1: images without labels ---
    missing_labels = img_stems - lbl_stems
    if missing_labels:
        for stem in sorted(missing_labels)[:10]:
            errors.append(f"[{split}] Imagem sem label: {stem}")
        if len(missing_labels) > 10:
            errors.append(
                f"[{split}] ... e mais {len(missing_labels) - 10} imagens sem label."
            )
    else:
        print("  Todas as imagens têm label correspondente ✓")

    # --- Check 2: labels without images ---
    orphan_labels = lbl_stems - img_stems
    if orphan_labels:
        for stem in sorted(orphan_labels)[:10]:
            warnings.append(f"[{split}] Label sem imagem correspondente: {stem}")
        if len(orphan_labels) > 10:
            warnings.append(
                f"[{split}] ... e mais {len(orphan_labels) - 10} labels sem imagem."
            )
    else:
        print("  Todos os labels têm imagem correspondente ✓")

    # --- Check 3-6: annotation content ---
    valid_ids = set(class_names.keys())
    class_counter: Counter = Counter()
    empty_labels = 0
    annotation_errors = 0

    for lbl_file in sorted(labels_dir.glob("*.txt")):
        content = lbl_file.read_text(encoding="utf-8").strip()
        if not content:
            empty_labels += 1
            warnings.append(f"[{split}] Label vazio (sem anotações): {lbl_file.name}")
            continue

        for lineno, line in enumerate(content.splitlines(), start=1):
            parts = line.split()

            # Check 3: field count
            if len(parts) != 5:
                errors.append(
                    f"[{split}] {lbl_file.name}:{lineno} — "
                    f"esperado 5 campos, encontrado {len(parts)}: '{line}'"
                )
                annotation_errors += 1
                continue

            # Parse
            try:
                cls_id = int(parts[0])
                xc, yc, bw, bh = map(float, parts[1:])
            except ValueError:
                errors.append(
                    f"[{split}] {lbl_file.name}:{lineno} — "
                    f"valores não numéricos: '{line}'"
                )
                annotation_errors += 1
                continue

            # Check 4: normalized coordinates in [0, 1]
            if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0
                    and 0.0 < bw <= 1.0 and 0.0 < bh <= 1.0):
                errors.append(
                    f"[{split}] {lbl_file.name}:{lineno} — "
                    f"coordenadas fora de [0,1]: "
                    f"xc={xc:.4f} yc={yc:.4f} w={bw:.4f} h={bh:.4f}"
                )
                annotation_errors += 1

            # Check 5: valid class id
            if cls_id not in valid_ids:
                errors.append(
                    f"[{split}] {lbl_file.name}:{lineno} — "
                    f"class_id={cls_id} não existe no data.yaml"
                )
                annotation_errors += 1
            else:
                class_counter[cls_id] += 1

    if annotation_errors == 0:
        print("  Todas as anotações são válidas ✓")
    else:
        print(f"  {annotation_errors} erro(s) de anotação encontrado(s) ✗")

    if empty_labels > 0:
        print(f"  {empty_labels} label(s) vazio(s) encontrado(s) (aviso)")

    return class_counter


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_class_distribution(
    counter: Counter,
    class_names: dict[int, str],
    split: str,
) -> None:
    total = sum(counter.values())
    if total == 0:
        return
    print(f"\n  Distribuição de classes — {split} ({total} anotações):")
    for cls_id in sorted(class_names):
        count = counter.get(cls_id, 0)
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"    [{cls_id:2d}] {class_names[cls_id]:<35s} "
              f"{count:6d}  {pct:5.1f}%  {bar}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida a consistência do dataset YOLO",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data", type=Path, default=DEFAULT_DATA_YAML,
        help="Caminho para data.yaml",
    )
    parser.add_argument(
        "--splits", nargs="+", default=["train", "val", "test"],
        help="Splits a verificar",
    )
    parser.add_argument(
        "--show-distribution", action="store_true", default=True,
        help="Exibir distribuição de classes por split",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Retornar exit code 1 se houver qualquer erro (útil em CI)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.data.exists():
        print(f"[ERROR] data.yaml não encontrado: {args.data}")
        sys.exit(1)

    dataset_root, class_names = load_data_yaml(args.data)
    print(f"data.yaml  : {args.data}")
    print(f"Dataset    : {dataset_root}")
    print(f"Classes    : {len(class_names)}")
    print(f"Splits     : {', '.join(args.splits)}")

    all_errors:   list[str] = []
    all_warnings: list[str] = []
    all_counters: dict[str, Counter] = {}

    for split in args.splits:
        counter = verify_split(
            split, dataset_root, class_names,
            all_errors, all_warnings,
        )
        all_counters[split] = counter

    # --- Class distribution ---
    if args.show_distribution:
        for split in args.splits:
            print_class_distribution(all_counters[split], class_names, split)

    # --- Final summary ---
    print(f"\n{'═'*55}")
    print("  RESUMO")
    print(f"{'═'*55}")

    if all_warnings:
        print(f"\n  Avisos ({len(all_warnings)}):")
        for w in all_warnings:
            print(f"    ⚠  {w}")

    if all_errors:
        print(f"\n  Erros ({len(all_errors)}):")
        for e in all_errors:
            print(f"    ✗  {e}")
        print(f"\n  {len(all_errors)} erro(s) encontrado(s).")
        if args.strict:
            sys.exit(1)
    else:
        print("\n  Dataset válido — nenhum erro encontrado. ✓")


if __name__ == "__main__":
    main()
