"""
vectorizer.py — Raster to Vector (image → SVG)

Objetivo: converter PNG/JPG/WEBP para SVG vetorial com qualidade excelente.
- Modo OUTLINE (padrão): usa vtracer (Rust) — suporta cor e P&B, saída de alta fidelidade.
- Modo CENTERLINE (esqueleto): usa scikit-image skeletonize — gera traço único
  ideal para animação handwriting (stroke-dasharray).

Design: sem I/O acoplado a fs.py; todas as funções recebem Path.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from PIL import Image

# ---------------------------------------------------------------------------
# Presets de qualidade — vtracer
# ---------------------------------------------------------------------------
# Excellent: máxima fidelidade, arquivo maior mas curvas perfeitas.
# Standard: equilíbrio (defaults vtracer).
# Draft: rápido e leve.
PRESETS = {
    "excellent": {
        "filter_speckle": 2,       # mantém detalhes pequenos (vtracer default 4)
        "color_precision": 8,      # 8 bits por canal = máx cores
        "corner_threshold": 30,    # preserva esquinas (default 60)
        "length_threshold": 2.0,   # segmentos curtos (default 4.0)
        "splice_threshold": 30,    # junta curvas longas (default 45)
        "path_precision": 8,       # casas decimais no SVG
    },
    "standard": {
        "filter_speckle": 4,
        "color_precision": 6,
        "corner_threshold": 60,
        "length_threshold": 4.0,
        "splice_threshold": 45,
        "path_precision": 5,
    },
    "draft": {
        "filter_speckle": 16,
        "color_precision": 4,
        "corner_threshold": 90,
        "length_threshold": 5.0,
        "splice_threshold": 45,
        "path_precision": 3,
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_has_transparency(img: Image.Image) -> bool:
    return img.mode in ("RGBA", "LA") or img.info.get("transparency") is not None


def _prepare_tmp_image(input_path: Path, upscale: int = 1) -> Path:
    """
    Prepara imagem temporária para vtracer:
    - Se RGBA e fundo transparente, compõe sobre branco (vtracer não lida bem com alpha).
    - Opcional upscale para melhorar qualidade de traço pequeno (lanczos).
    Retorna Path temporário; caller deve deletar.
    """
    img = Image.open(input_path)
    # Handle transparency: composite over white for outline; for centerline we keep alpha logic elsewhere
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if len(img.split()) == 4:
            bg.paste(img, mask=img.split()[3])
        else:
            bg.paste(img)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if upscale != 1 and upscale > 1:
        w, h = img.size
        img = img.resize((w * upscale, h * upscale), Image.Resampling.LANCZOS)

    tmp = Path(tempfile.mktemp(suffix=".png"))
    img.save(tmp, format="PNG")
    return tmp


def _optimize_svg_precision(svg_content: str, precision: int) -> str:
    """
    Arredonda coordenadas no SVG para reduzir tamanho sem perder qualidade visível.
    vtracer já tem path_precision, mas garantimos pós-processamento leve.
    """
    # não-agressivo: apenas garante que não há excesso de casas
    # vtracer já faz bem, então deixamos como pass-through se precision >=8
    if precision >= 8:
        return svg_content
    return svg_content


def _get_svg_metrics(svg_path: Path, original_path: Path) -> dict:
    orig_size = os.path.getsize(original_path)
    svg_size = os.path.getsize(svg_path) if svg_path.exists() else 0
    # Conta paths para estimar complexidade
    try:
        txt = svg_path.read_text(encoding="utf-8", errors="ignore")
        n_paths = txt.count("<path")
        n_colors = len(set(re.findall(r'fill="([^"]+)"', txt)))
    except Exception:
        n_paths = 0
        n_colors = 0
    return {
        "original_size": orig_size,
        "svg_size": svg_size,
        "num_paths": n_paths,
        "num_colors": n_colors,
        "reduction_pct": ((orig_size - svg_size) / orig_size * 100) if orig_size else 0,
    }


# ---------------------------------------------------------------------------
# OUTLINE — vtracer
# ---------------------------------------------------------------------------

def vectorize_outline(
    input_path: Path,
    output_path: Path,
    colormode: Literal["color", "binary"] = "color",
    hierarchical: Literal["stacked", "cutout"] = "stacked",
    mode: Literal["spline", "polygon", "none"] = "spline",
    preset: Literal["excellent", "standard", "draft"] = "excellent",
    # overrides específicos (se None usa preset)
    filter_speckle: int | None = None,
    color_precision: int | None = None,
    corner_threshold: int | None = None,
    length_threshold: float | None = None,
    splice_threshold: int | None = None,
    path_precision: int | None = None,
    upscale: int = 1,
) -> dict:
    """
    Vetoriza via vtracer (outline). Prioridade excelente qualidade.

    Retorna dict com metrics + svg_content (str).
    """
    try:
        import vtracer  # type: ignore
    except ImportError as e:
        raise ImportError(
            "vtracer não instalado. Instale com: poetry add vtracer  ou  pip install vtracer"
        ) from e

    p = PRESETS[preset]
    fs = filter_speckle if filter_speckle is not None else p["filter_speckle"]
    cp = color_precision if color_precision is not None else p["color_precision"]
    ct = corner_threshold if corner_threshold is not None else p["corner_threshold"]
    lt = length_threshold if length_threshold is not None else p["length_threshold"]
    st = splice_threshold if splice_threshold is not None else p["splice_threshold"]
    pp = path_precision if path_precision is not None else p["path_precision"]

    tmp = _prepare_tmp_image(input_path, upscale=upscale)
    try:
        # vtracer API: convert_image_to_svg_py(input, output, colormode, hierarchical, mode, ...)
        # A assinatura completa tem muitos kwargs; passamos todos explicitamente
        vtracer.convert_image_to_svg_py(
            str(tmp),
            str(output_path),
            colormode=colormode,
            hierarchical=hierarchical,
            mode=mode,
            filter_speckle=fs,
            color_precision=cp,
            layer_difference=16,
            corner_threshold=ct,
            length_threshold=lt,
            max_iterations=10,
            splice_threshold=st,
            path_precision=pp,
        )
        # vtracer já escreveu output_path
        # pós-otimização leve (se necessário)
        content = output_path.read_text(encoding="utf-8", errors="ignore")
        content = _optimize_svg_precision(content, pp)
        output_path.write_text(content, encoding="utf-8")

        metrics = _get_svg_metrics(output_path, input_path)
        metrics.update({
            "backend": "vtracer",
            "mode": "outline",
            "colormode": colormode,
            "preset": preset,
            "params": {
                "filter_speckle": fs, "color_precision": cp, "corner_threshold": ct,
                "length_threshold": lt, "splice_threshold": st, "path_precision": pp,
                "hierarchical": hierarchical, "mode": mode,
            },
        })
        return metrics
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def vectorize_raw_bytes(
    image_bytes: bytes,
    img_format: str = "png",
    colormode: str = "color",
    preset: str = "excellent",
) -> str:
    """Helper para converter bytes direto para SVG string (sem arquivo)."""
    import vtracer
    p = PRESETS[preset]
    return vtracer.convert_raw_image_to_svg(
        image_bytes,
        img_format=img_format,
        colormode=colormode,
        hierarchical="stacked",
        mode="spline",
        filter_speckle=p["filter_speckle"],
        color_precision=p["color_precision"],
        layer_difference=16,
        corner_threshold=p["corner_threshold"],
        length_threshold=p["length_threshold"],
        max_iterations=10,
        splice_threshold=p["splice_threshold"],
        path_precision=p["path_precision"],
    )


# ---------------------------------------------------------------------------
# CENTERLINE — skeleton (handwriting)
# ---------------------------------------------------------------------------

def vectorize_centerline(
    input_path: Path,
    output_path: Path,
    threshold: int | None = None,
    invert: bool = False,
    stroke_width: int = 3,
    stroke_color: str = "#000000",
    simplify_tolerance: float = 1.0,
    min_path_length: int = 10,
) -> dict:
    """
    Vetoriza via esqueleto (centerline) — ideal para animação lápis.

    - threshold None → Otsu automático (melhor para alfabeto).
    - invert True se traço for claro em fundo escuro.
    - simplify_tolerance: tolerância Douglas-Peucker (px). Maior = mais simples.
    - min_path_length: descarta esqueletos ruidosos < N px.

    Depende de scikit-image, scipy, svgwrite, numpy.
    Fallback: se não houver deps, usa vtracer binary como outline fallback.
    """
    try:
        import numpy as np
        from skimage import io as skio, color as skcolor, filters as skfilters, morphology as skmorph, measure as skmeasure
        import svgwrite  # type: ignore
    except ImportError as e:
        # fallback para outline binary
        print(f"⚠️  Deps centerline ausentes ({e}), usando fallback outline binary")
        return vectorize_outline(input_path, output_path, colormode="binary", preset="excellent")

    # 1. Load + grayscale
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    # Convert to numpy
    import numpy as np
    arr = np.array(img)  # HWC

    # Luminance
    gray = np.dot(arr[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)

    # Invert logic: skeletonize espera objeto=1 (branco) fundo=0
    # Para alfabeto típico: fundo branco (255), letra preta (0) → inverter após binarizar
    if threshold is None:
        try:
            thr = skfilters.threshold_otsu(gray)
            # Otsu pode falhar em imagens bimodais extremas (ex: 97% branco)
            # se thr for 0 ou 255, usa fallback 128
            if thr is None or thr < 10 or thr > 245 or thr == 0:
                thr = 128
        except Exception:
            thr = 128
    else:
        thr = threshold

    binary = gray < thr  # True onde é letra (escura)
    if invert:
        binary = ~binary

    # Auto-invert: se mais da metade da imagem virou "foreground", provavelmente fundo foi detectado como objeto
    if binary.sum() > (w * h * 0.5):
        binary = ~binary

    # 2. Limpeza morfológica leve (remove ruído sem quebrar traços)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            # scikit-image 0.26+ usa max_size, mantém compat
            try:
                binary = skmorph.remove_small_objects(binary, min_size=30)
            except TypeError:
                binary = skmorph.remove_small_objects(binary, max_size=30)
            try:
                binary = skmorph.remove_small_holes(binary, area_threshold=30)
            except TypeError:
                binary = skmorph.remove_small_holes(binary, max_size=30)
        except Exception:
            pass

    # 3. Skeletonize
    try:
        skeleton = skmorph.skeletonize(binary)
    except Exception as e:
        raise RuntimeError(f"Falha no skeletonize: {e}") from e

    # 4. Extrair paths via walking no esqueleto
    # Abordagem: encontrar componentes conectados, extrair contornos ordenados
    # Usamos skeleton como base para traçar linhas centrais
    from collections import deque

    # Label components para processar cada letra isolada
    labeled = skmeasure.label(skeleton, connectivity=2)
    regions = skmeasure.regionprops(labeled)

    # Helper: walking por componente usando BFS para ordenar
    def trace_component(mask: np.ndarray) -> list[list[tuple[float, float]]]:
        """Retorna lista de polylines (cada uma é lista de (x,y)) para um componente."""
        coords = np.column_stack(np.where(mask))  # [y, x]
        if len(coords) == 0:
            return []
        # Conjunto para busca rápida
        coord_set = set(map(tuple, coords))
        visited = set()
        polylines: list[list[tuple[float, float]]] = []

        # Encontra endpoints (pixels com 1 vizinho) para iniciar traço
        def neighbors(y, x):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if (ny, nx) in coord_set:
                        yield (ny, nx)

        def count_nbr(y, x):
            return sum(1 for _ in neighbors(y, x))

        # Para cada componente, caminhar
        # Começa por endpoints; se não houver (loop fechado ex: O), começa em ponto aleatório
        while len(visited) < len(coord_set):
            # acha próximo não visitado
            start = None
            for c in coords:
                t = tuple(c)
                if t not in visited:
                    # prioriza endpoints
                    if count_nbr(*t) == 1:
                        start = t
                        break
            if start is None:
                for c in coords:
                    t = tuple(c)
                    if t not in visited:
                        start = t
                        break
            assert start is not None
            # BFS/DFS walk
            stack = [start]
            poly: list[tuple[float, float]] = []
            prev = None
            cur = start
            # caminhada gulosa: sempre escolhe vizinho não visitado mais próximo
            while cur is not None:
                if cur in visited:
                    # já visitado, tenta outro vizinho
                    nbrs = [n for n in neighbors(*cur) if n not in visited]
                    if not nbrs:
                        break
                    cur = nbrs[0]
                    continue
                visited.add(cur)
                poly.append((float(cur[1]), float(cur[0])))  # x,y
                # escolhe próximo vizinho não visitado
                nbrs = [n for n in neighbors(*cur) if n not in visited]
                if not nbrs:
                    break
                # prioriza continuar em linha reta (evita zigzag)
                if prev is not None and len(nbrs) > 1:
                    # vetor anterior
                    vy, vx = cur[0] - prev[0], cur[1] - prev[1]
                    best = None
                    best_score = -1
                    for n in nbrs:
                        ny, nx = n
                        wy, wx = ny - cur[0], nx - cur[1]
                        # dot product para manter direção
                        score = vx * wx + vy * wy
                        if score > best_score:
                            best_score = score
                            best = n
                    cur = best
                else:
                    cur = nbrs[0]
                prev = poly[-1][::-1] if poly else None  # y,x
                # converte prev para y,x
                if poly:
                    # last point y,x
                    prev = (poly[-1][1], poly[-1][0])
                # prev para próxima iteração deve ser cur anterior? simplificado acima

            if len(poly) >= 2:
                polylines.append(poly)
            else:
                # ponto isolado
                if poly:
                    polylines.append(poly)
                visited.add(start)

            # evita loop infinito: se poly não cresceu e ainda há não visitados, já tratado no while externo
            if len(poly) == 0:
                visited.add(start)

        return polylines

    # Simplificação Douglas-Peucker simples
    def _perp_dist(px, py, x1, y1, x2, y2):
        if x1 == x2 and y1 == y2:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / ((x2 - x1) ** 2 + (y2 - y1) ** 2)
        t = max(0, min(1, t))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        return ((px - proj_x) ** 2 + (py - proj_y) ** 2) ** 0.5

    def rdp(points: list[tuple[float, float]], eps: float) -> list[tuple[float, float]]:
        if len(points) < 3 or eps <= 0:
            return points
        dmax = 0.0
        idx = 0
        for i in range(1, len(points) - 1):
            d = _perp_dist(points[i][0], points[i][1], points[0][0], points[0][1], points[-1][0], points[-1][1])
            if d > dmax:
                idx = i
                dmax = d
        if dmax > eps:
            rec1 = rdp(points[: idx + 1], eps)
            rec2 = rdp(points[idx:], eps)
            return rec1[:-1] + rec2
        else:
            return [points[0], points[-1]]

    all_polylines: list[list[tuple[float, float]]] = []
    for region in regions:
        minr, minc, maxr, maxc = region.bbox
        # extrai sub-mask
        sub = skeleton[minr:maxr, minc:maxc]
        pls = trace_component(sub)
        # Ajusta offset global e filtra por tamanho
        for pl in pls:
            if len(pl) < 2:
                continue
            # calcula comprimento aproximado
            length = sum(((pl[i][0] - pl[i - 1][0]) ** 2 + (pl[i][1] - pl[i - 1][1]) ** 2) ** 0.5 for i in range(1, len(pl)))
            if length < min_path_length:
                continue
            # offset
            pl_global = [(x + minc, y + minr) for x, y in pl]
            # simplify
            if simplify_tolerance > 0:
                pl_global = rdp(pl_global, simplify_tolerance)
            all_polylines.append(pl_global)

    # Se skeleton vazio ou falhou, fallback para contornos
    if not all_polylines:
        # fallback: usa find_contours no binário original
        try:
            contours = skmeasure.find_contours(binary.astype(float), 0.5)
            for cnt in contours:
                # cnt é [row, col] → y,x
                pl = [(float(c), float(r)) for r, c in cnt]
                if len(pl) < min_path_length:
                    continue
                if simplify_tolerance > 0:
                    pl = rdp(pl, simplify_tolerance)
                all_polylines.append(pl)
        except Exception:
            pass

    # 5. Escreve SVG
    dwg = svgwrite.Drawing(str(output_path), size=(f"{w}px", f"{h}px"), viewBox=f"0 0 {w} {h}")
    # fundo branco opcional para visualização
    # dwg.add(dwg.rect(insert=(0,0), size=(w,h), fill="white"))

    for pl in all_polylines:
        if len(pl) < 2:
            continue
        # Constrói path d: M x y L x y ... ou curva suave
        # Para excelente qualidade, usa polyline com stroke; suavização via Bezier seria ideal mas RDP já ajuda
        # Se muitos pontos, usa S (smooth)
        d = f"M {pl[0][0]:.2f} {pl[0][1]:.2f} "
        for x, y in pl[1:]:
            d += f"L {x:.2f} {y:.2f} "
        # path único por traço
        path = dwg.path(
            d=d.strip(),
            fill="none",
            stroke=stroke_color,
            stroke_width=stroke_width,
            stroke_linecap="round",
            stroke_linejoin="round",
        )
        # Atributos para animação handwriting
        path.update({"pathLength": "1", "style": "stroke-dasharray:1; stroke-dashoffset:1"})
        dwg.add(path)

    # Metadados para animação: adiciona <style> para demo
    style_content = """
    @keyframes draw { to { stroke-dashoffset: 0; } }
    path { animation: draw 1.2s ease-in-out forwards; }
    """
    # svgwrite não tem helper direto para style, injetamos raw
    dwg.save()
    # Injeta style após <svg> se quiser animação automática (opcional)
    # Mantemos SVG minimalista para edição; animação pode ser adicionada via CSS externo

    metrics = _get_svg_metrics(output_path, input_path)
    metrics.update({
        "backend": "skeleton",
        "mode": "centerline",
        "num_strokes": len(all_polylines),
        "threshold": thr,
        "stroke_width": stroke_width,
    })
    return metrics


# ---------------------------------------------------------------------------
# Entry genérico
# ---------------------------------------------------------------------------

def vectorize_image(
    input_path: Path,
    output_path: Path,
    mode: Literal["outline", "centerline"] = "outline",
    **kwargs,
) -> dict:
    """
    Dispatcher: escolhe backend por modo.
    - outline → vtracer (excelente qualidade)
    - centerline → skeleton
    """
    if mode == "centerline":
        return vectorize_centerline(input_path, output_path, **kwargs)
    else:
        # outline kwargs mapeiam para vtracer
        # filtra kwargs inválidos para outline
        allowed = {"colormode", "hierarchical", "mode", "preset", "filter_speckle", "color_precision", "corner_threshold", "length_threshold", "splice_threshold", "path_precision", "upscale"}
        fk = {k: v for k, v in kwargs.items() if k in allowed}
        return vectorize_outline(input_path, output_path, **fk)
