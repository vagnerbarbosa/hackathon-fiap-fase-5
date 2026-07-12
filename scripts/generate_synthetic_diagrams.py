"""
generate_synthetic_diagrams.py
================================
Gera diagramas sintéticos de arquitetura de software com anotações YOLO.

Uso:
    python scripts/generate_synthetic_diagrams.py [--output dataset/train] [--count 50] [--seed 42]

Saída:
    <output>/images/<uuid>-synth_<n>.png
    <output>/labels/<uuid>-synth_<n>.txt

Cada arquivo .txt segue o formato YOLO:
    <class_id> <x_center> <y_center> <width> <height>   (valores normalizados 0-1)

As classes geradas correspondem ao data.yaml do projeto (32 classes).
"""

from __future__ import annotations

import argparse
import math
import random
import uuid
from pathlib import Path

# Pillow is the only runtime dependency (already in requirements-notebook.txt)
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Class taxonomy — must match dataset/data.yaml
# ---------------------------------------------------------------------------
CLASS_NAMES: dict[int, str] = {
    0:  "actor_user",
    1:  "actor_admin",
    2:  "edge_ddos_protection",
    3:  "edge_cdn",
    4:  "edge_waf",
    5:  "edge_gateway",
    6:  "edge_portal",
    7:  "external_entry_point",
    8:  "integration_orchestrator",
    9:  "integration_messaging",
    10: "compute_load_balancer",
    11: "compute_service",
    12: "compute_worker",
    13: "data_database",
    14: "data_cache",
    15: "data_storage",
    16: "security_identity_provider",
    17: "security_key_management",
    18: "obs_monitoring",
    19: "obs_audit",
    20: "external_backend_service",
    21: "external_saas_service",
    22: "external_web_service",
    23: "communication_service",
    24: "backup_service",
    25: "boundary_cloud",
    26: "boundary_region",
    27: "boundary_resource_group",
    28: "boundary_vpc_or_vnet",
    29: "boundary_subnet_public",
    30: "boundary_subnet_private",
    31: "boundary_autoscaling_group",
}

# Colours per category (R, G, B)
_CATEGORY_COLOURS: dict[str, tuple[int, int, int]] = {
    "actor":       (70,  130, 180),
    "edge":        (255, 165,   0),
    "integration": (148,  0,  211),
    "compute":     (34,  139,  34),
    "data":        (220,  20,  60),
    "security":    (255,  69,   0),
    "obs":         (100, 149, 237),
    "external":    (169, 169, 169),
    "communication": (0, 206, 209),
    "backup":      (255, 215,   0),
    "boundary":    (200, 200, 200),
}

# Boundary classes — drawn as rectangles *behind* node components
BOUNDARY_CLASSES: set[int] = {25, 26, 27, 28, 29, 30, 31}
# Node classes — drawn as boxes with labels
NODE_CLASSES: list[int] = [c for c in CLASS_NAMES if c not in BOUNDARY_CLASSES]

# Minimum node box size in pixels (at 640×640 canvas)
_NODE_W = 80
_NODE_H = 50
_MARGIN = 20
_CANVAS = (800, 600)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _category(class_id: int) -> str:
    prefix = CLASS_NAMES[class_id].split("_")[0]
    return prefix


def _colour(class_id: int) -> tuple[int, int, int]:
    cat = _category(class_id)
    return _CATEGORY_COLOURS.get(cat, (120, 120, 120))


def _try_load_font(size: int = 11) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a truetype font if available, fall back to default."""
    candidates = [
        "arial.ttf", "Arial.ttf",
        "DejaVuSans.ttf", "dejavusans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _place_nodes(
    n_nodes: int,
    canvas_w: int,
    canvas_h: int,
    node_w: int,
    node_h: int,
    margin: int,
    rng: random.Random,
) -> list[tuple[int, int]]:
    """Return (x1, y1) top-left corners for n_nodes non-overlapping boxes."""
    positions: list[tuple[int, int]] = []
    max_attempts = 1000
    attempts = 0

    def overlaps(x1: int, y1: int) -> bool:
        for px, py in positions:
            if abs(x1 - px) < node_w + margin and abs(y1 - py) < node_h + margin:
                return True
        return False

    while len(positions) < n_nodes and attempts < max_attempts:
        x = rng.randint(margin, canvas_w - node_w - margin)
        y = rng.randint(margin, canvas_h - node_h - margin)
        if not overlaps(x, y):
            positions.append((x, y))
        attempts += 1

    return positions


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    x1: int, y1: int,
    x2: int, y2: int,
    colour: tuple[int, int, int] = (80, 80, 80),
    width: int = 2,
) -> None:
    """Draw a simple arrow from (x1,y1) to (x2,y2)."""
    draw.line([(x1, y1), (x2, y2)], fill=colour, width=width)
    # arrowhead
    angle = math.atan2(y2 - y1, x2 - x1)
    head_len = 10
    head_angle = math.pi / 6
    for sign in (+1, -1):
        ax = x2 - head_len * math.cos(angle - sign * head_angle)
        ay = y2 - head_len * math.sin(angle - sign * head_angle)
        draw.line([(x2, y2), (int(ax), int(ay))], fill=colour, width=width)


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------

def generate_diagram(
    rng: random.Random,
    canvas_size: tuple[int, int] = _CANVAS,
    node_w: int = _NODE_W,
    node_h: int = _NODE_H,
    margin: int = _MARGIN,
    min_nodes: int = 3,
    max_nodes: int = 10,
    add_boundary: bool = True,
) -> tuple[Image.Image, list[tuple[int, int, int, int, int]]]:
    """
    Generate one synthetic architecture diagram.

    Returns
    -------
    image : PIL.Image (RGB)
    annotations : list of (class_id, x_center_px, y_center_px, w_px, h_px)
        in *pixel* coordinates (not yet normalised).
    """
    cw, ch = canvas_size
    # Background: light grey / white with subtle grid
    bg_colour = rng.choice([(255, 255, 255), (245, 245, 245), (240, 248, 255)])
    img = Image.new("RGB", (cw, ch), color=bg_colour)
    draw = ImageDraw.Draw(img)
    font = _try_load_font(10)
    font_title = _try_load_font(9)

    annotations: list[tuple[int, int, int, int, int]] = []

    # --- Optional boundary rectangle (drawn first / behind nodes) ---
    if add_boundary and rng.random() < 0.6:
        b_cls = rng.choice(list(BOUNDARY_CLASSES))
        bx1 = rng.randint(5, 40)
        by1 = rng.randint(5, 40)
        bx2 = rng.randint(cw - 40, cw - 5)
        by2 = rng.randint(ch - 40, ch - 5)
        b_colour = _colour(b_cls)
        draw.rectangle(
            [(bx1, by1), (bx2, by2)],
            outline=b_colour,
            width=2,
        )
        # Dashed effect (draw short lines)
        for dx in range(bx1, bx2, 10):
            draw.line([(dx, by1), (min(dx + 5, bx2), by1)], fill=b_colour, width=1)
            draw.line([(dx, by2), (min(dx + 5, bx2), by2)], fill=b_colour, width=1)
        draw.text((bx1 + 4, by1 + 2), CLASS_NAMES[b_cls], fill=b_colour, font=font_title)

        bcx = (bx1 + bx2) // 2
        bcy = (by1 + by2) // 2
        bw = bx2 - bx1
        bh = by2 - by1
        annotations.append((b_cls, bcx, bcy, bw, bh))

    # --- Node placement ---
    n_nodes = rng.randint(min_nodes, max_nodes)
    node_cls_ids = rng.choices(NODE_CLASSES, k=n_nodes)
    positions = _place_nodes(n_nodes, cw, ch, node_w, node_h, margin, rng)
    if len(positions) < n_nodes:
        n_nodes = len(positions)
        node_cls_ids = node_cls_ids[:n_nodes]

    node_centres: list[tuple[int, int]] = []
    for (x1, y1), cls_id in zip(positions, node_cls_ids):
        x2, y2 = x1 + node_w, y1 + node_h
        colour = _colour(cls_id)
        fill_alpha = (colour[0], colour[1], colour[2])

        # Box with lighter fill
        fill_light = tuple(min(255, int(c * 0.3 + 255 * 0.7)) for c in colour)
        draw.rectangle([(x1, y1), (x2, y2)], fill=fill_light, outline=colour, width=2)  # type: ignore[arg-type]

        # Icon stub — small coloured circle in the box
        icon_r = 8
        ix, iy = x1 + 12, y1 + node_h // 2
        draw.ellipse([(ix - icon_r, iy - icon_r), (ix + icon_r, iy + icon_r)], fill=colour)

        # Label (truncated to fit)
        label = CLASS_NAMES[cls_id].replace("_", "\n")
        draw.text((x1 + 26, y1 + 4), label, fill=(30, 30, 30), font=font)

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        node_centres.append((cx, cy))
        annotations.append((cls_id, cx, cy, node_w, node_h))

    # --- Random edges between nodes ---
    if n_nodes >= 2:
        n_edges = rng.randint(n_nodes - 1, min(n_nodes * 2, n_nodes + 5))
        drawn: set[frozenset[int]] = set()
        for _ in range(n_edges * 3):
            if len(drawn) >= n_edges:
                break
            i, j = rng.sample(range(n_nodes), 2)
            key: frozenset[int] = frozenset({i, j})
            if key in drawn:
                continue
            drawn.add(key)
            cx1, cy1 = node_centres[i]
            cx2, cy2 = node_centres[j]
            _draw_arrow(draw, cx1, cy1, cx2, cy2)

    return img, annotations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic architecture diagrams")
    parser.add_argument(
        "--output", default="dataset/train", type=Path,
        help="Destination directory (images/ and labels/ sub-dirs are created automatically)"
    )
    parser.add_argument("--count", default=50, type=int, help="Number of diagrams to generate")
    parser.add_argument("--seed", default=42, type=int, help="Random seed (RNF-02)")
    parser.add_argument("--width",  default=800, type=int, help="Canvas width in pixels")
    parser.add_argument("--height", default=600, type=int, help="Canvas height in pixels")
    parser.add_argument(
        "--min-nodes", default=3, type=int, dest="min_nodes",
        help="Minimum components per diagram (RF-01)"
    )
    parser.add_argument(
        "--max-nodes", default=10, type=int, dest="max_nodes",
        help="Maximum components per diagram (RF-01)"
    )
    args = parser.parse_args()

    out_dir: Path = args.output
    images_dir = out_dir / "images"
    labels_dir = out_dir / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    canvas = (args.width, args.height)
    generated = 0

    for i in range(args.count):
        stem = f"{uuid.uuid4().hex[:8]}-synth_{i}"
        img_path = images_dir / f"{stem}.png"
        lbl_path = labels_dir / f"{stem}.txt"

        img, annotations = generate_diagram(
            rng=rng,
            canvas_size=canvas,
            min_nodes=args.min_nodes,
            max_nodes=args.max_nodes,
        )

        # Ensure minimum resolution (RNF-01: 640x480)
        if img.width < 640 or img.height < 480:
            img = img.resize((max(640, img.width), max(480, img.height)), Image.LANCZOS)

        img.save(img_path, format="PNG", optimize=True)

        # Write YOLO labels (normalised coordinates)
        w, h = img.size
        lines: list[str] = []
        for cls_id, cx, cy, bw, bh in annotations:
            nx = cx / w
            ny = cy / h
            nw = bw / w
            nh = bh / h
            # Clamp to [0, 1]
            nx = max(0.0, min(1.0, nx))
            ny = max(0.0, min(1.0, ny))
            nw = max(0.001, min(1.0, nw))
            nh = max(0.001, min(1.0, nh))
            lines.append(f"{cls_id} {nx:.6f} {ny:.6f} {nw:.6f} {nh:.6f}")

        lbl_path.write_text("\n".join(lines), encoding="utf-8")
        generated += 1

        if (i + 1) % 10 == 0 or i == args.count - 1:
            print(f"  [{i+1:4d}/{args.count}] {img_path.name}")

    print(f"\nDone. Generated {generated} diagrams → {out_dir}")


if __name__ == "__main__":
    main()
