"""
train_yolo.py
=============
CLI de treinamento YOLOv11n para detecção de componentes de arquitetura.

Uso rápido (a partir da raiz do repositório):

    python scripts/train_yolo.py

Exemplos com opções:

    # GPU, 100 epochs, batch 16 (padrão)
    python scripts/train_yolo.py --epochs 100 --batch 16 --device 0

    # CPU, rodar rápido para sanity-check
    python scripts/train_yolo.py --epochs 5 --batch 8 --device cpu --run-name debug

    # Retomar treino interrompido
    python scripts/train_yolo.py --resume runs/train/yolo11n_arch_components/weights/last.pt

Hiperparâmetros usados (RF-05 da Spec 002):
    epochs   : 100
    imgsz    : 640
    batch    : 16
    patience : 20  (early stopping)
    seed     : 42

Saídas (RF-06):
    runs/train/<run-name>/weights/best.pt   — melhor checkpoint PyTorch
    runs/train/<run-name>/weights/last.pt   — último checkpoint
    models/best.pt                          — cópia para uso pela Spec 003
    models/best.onnx                        — exportação ONNX otimizada
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path

import numpy as np
import torch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_YAML = REPO_ROOT / "dataset" / "data.yaml"
MODELS_DIR = REPO_ROOT / "models"


def _set_seeds(seed: int) -> None:
    """Fixa seeds para reprodutibilidade (RNF-02)."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _copy_artefacts(run_dir: Path) -> None:
    """Copia best.pt e best.onnx para models/ (contrato de saída da Spec 002)."""
    MODELS_DIR.mkdir(exist_ok=True)

    best_pt = run_dir / "weights" / "best.pt"
    if best_pt.exists():
        dest = MODELS_DIR / "best.pt"
        shutil.copy2(best_pt, dest)
        print(f"  Saved  best.pt  → {dest}")
    else:
        print(f"  [WARN] best.pt not found at {best_pt}")

    # ONNX é gerado pelo export() logo abaixo e fica ao lado de best.pt
    src_onnx = run_dir / "weights" / "best.onnx"
    if src_onnx.exists():
        dest = MODELS_DIR / "best.onnx"
        shutil.copy2(src_onnx, dest)
        print(f"  Saved  best.onnx → {dest}")


def _print_metrics(metrics) -> None:
    """Imprime resumo de métricas e alerta se RNF-03 não for atingido."""
    map50    = metrics.box.map50
    map50_95 = metrics.box.map
    prec     = metrics.box.mp
    rec      = metrics.box.mr

    print("\n===== Validation metrics =====")
    print(f"  mAP@0.5       : {map50:.4f}   (target > 0.75)")
    print(f"  mAP@0.5:0.95  : {map50_95:.4f}   (target > 0.50)")
    print(f"  Precision     : {prec:.4f}")
    print(f"  Recall        : {rec:.4f}")

    if map50 < 0.75:
        print(
            f"\n  [WARN] mAP@0.5 {map50:.4f} < 0.75 (RNF-03). "
            "Considere mais epochs ou mais dados."
        )
    else:
        print(f"\n  mAP@0.5 target atingido.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tuning YOLOv11n para detecção de componentes de arquitetura",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Dataset / model
    parser.add_argument(
        "--data", type=Path, default=DATA_YAML,
        help="Caminho para data.yaml",
    )
    parser.add_argument(
        "--weights", default="yolo11n.pt",
        help="Pesos iniciais: 'yolo11n.pt' (COCO) ou caminho para .pt customizado",
    )
    parser.add_argument(
        "--resume", type=Path, default=None,
        help="Retomar treino a partir de last.pt",
    )

    # Hyperparameters (RF-05)
    parser.add_argument("--epochs",   type=int,   default=100)
    parser.add_argument("--imgsz",    type=int,   default=640)
    parser.add_argument("--batch",    type=int,   default=16)
    parser.add_argument("--patience", type=int,   default=20,
                        help="Early stopping: epochs sem melhora antes de parar")
    parser.add_argument("--device",   default="0" if torch.cuda.is_available() else "cpu",
                        help="'0' para GPU 0, 'cpu' para CPU, '0,1' para multi-GPU")
    parser.add_argument("--seed",     type=int,   default=42)

    # Output
    parser.add_argument(
        "--run-name", default="yolo11n_arch_components",
        help="Nome da pasta de run dentro de runs/train/",
    )
    parser.add_argument(
        "--project", type=Path,
        default=REPO_ROOT / "runs" / "train",
        help="Pasta raiz onde os runs são salvos",
    )

    # Flags
    parser.add_argument(
        "--no-export", action="store_true",
        help="Pular exportação ONNX após o treino",
    )
    parser.add_argument(
        "--export-only", type=Path, default=None, metavar="BEST_PT",
        help="Apenas exportar best.pt existente para ONNX (sem treinar)",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Importar aqui para que `--help` funcione mesmo sem ultralytics instalado
    try:
        from ultralytics import YOLO
    except ImportError:
        print(
            "[ERROR] ultralytics não instalado.\n"
            "  Execute: pip install -r requirements-notebook.txt"
        )
        sys.exit(1)

    _set_seeds(args.seed)

    # ------------------------------------------------------------------
    # Modo export-only
    # ------------------------------------------------------------------
    if args.export_only is not None:
        pt_path = args.export_only
        if not pt_path.exists():
            print(f"[ERROR] Arquivo não encontrado: {pt_path}")
            sys.exit(1)
        print(f"Exportando {pt_path} → ONNX …")
        model = YOLO(str(pt_path))
        model.export(format="onnx", imgsz=args.imgsz, opset=17, simplify=True)
        # Copia para models/
        src_onnx = pt_path.with_suffix(".onnx")
        if src_onnx.exists():
            dest = MODELS_DIR / "best.onnx"
            MODELS_DIR.mkdir(exist_ok=True)
            shutil.copy2(src_onnx, dest)
            print(f"  Saved  best.onnx → {dest}")
        return

    # ------------------------------------------------------------------
    # Modo resume
    # ------------------------------------------------------------------
    if args.resume is not None:
        if not args.resume.exists():
            print(f"[ERROR] Checkpoint não encontrado: {args.resume}")
            sys.exit(1)
        print(f"Retomando treino a partir de {args.resume} …")
        model = YOLO(str(args.resume))
        train_results = model.train(resume=True)
    else:
        # ------------------------------------------------------------------
        # Treino do zero (fine-tuning)
        # ------------------------------------------------------------------
        if not args.data.exists():
            print(f"[ERROR] data.yaml não encontrado: {args.data}")
            sys.exit(1)

        print("=" * 60)
        print("  YOLOv11n — Fine-tuning")
        print("=" * 60)
        print(f"  data     : {args.data}")
        print(f"  weights  : {args.weights}")
        print(f"  epochs   : {args.epochs}  (patience={args.patience})")
        print(f"  imgsz    : {args.imgsz}")
        print(f"  batch    : {args.batch}")
        print(f"  device   : {args.device}")
        print(f"  seed     : {args.seed}")
        print(f"  run      : {args.project / args.run_name}")
        print("=" * 60)

        model = YOLO(args.weights)

        train_results = model.train(
            data=str(args.data),
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            patience=args.patience,
            project=str(args.project),
            name=args.run_name,
            seed=args.seed,
            # Augmentation — moderada para preservar legibilidade dos diagramas
            hsv_h=0.01,
            hsv_s=0.5,
            hsv_v=0.4,
            degrees=0.0,     # diagramas raramente aparecem rotacionados
            translate=0.1,
            scale=0.4,
            fliplr=0.0,      # diagramas têm semântica esquerda-direita
            mosaic=1.0,
            close_mosaic=10,
            verbose=True,
            plots=True,
            save=True,
            save_period=10,
            exist_ok=True,
        )

    run_dir = Path(train_results.save_dir)
    print(f"\nTreino concluído. Artefatos em: {run_dir}")

    # ------------------------------------------------------------------
    # Validação (RNF-03)
    # ------------------------------------------------------------------
    best_pt = run_dir / "weights" / "best.pt"
    best_model = YOLO(str(best_pt))

    val_metrics = best_model.val(
        data=str(args.data),
        split="val",
        imgsz=args.imgsz,
        device=args.device,
        verbose=False,
    )
    _print_metrics(val_metrics)

    # ------------------------------------------------------------------
    # Exportação ONNX (RF-06)
    # ------------------------------------------------------------------
    if not args.no_export:
        print("\nExportando para ONNX …")
        best_model.export(
            format="onnx",
            imgsz=args.imgsz,
            opset=17,
            simplify=True,
            dynamic=False,
        )

    # ------------------------------------------------------------------
    # Copia artefatos para models/
    # ------------------------------------------------------------------
    print("\nCopiando artefatos para models/ …")
    _copy_artefacts(run_dir)

    print("\nPronto!")
    print(f"  best.pt   → {MODELS_DIR / 'best.pt'}")
    print(f"  best.onnx → {MODELS_DIR / 'best.onnx'}")


if __name__ == "__main__":
    main()
