#!/usr/bin/env python3
"""
gif_black_bg.py — gera cópias de GIFs com fundo preto, dimensionadas para o LCD.

Para cada arquivo *.gif no diretório de entrada (ignorando os que já contêm o
sufixo de saída), produz um novo GIF onde:
  - cada frame é compositado sobre um fundo preto sólido (rasterizando alfa);
  - o conteúdo é redimensionado proporcionalmente (LANCZOS) para caber no
    canvas alvo (default 320x320, resolução do LCD do NZXT Kraken 2023);
  - o resultado é salvo com o mesmo timing por frame e loop count do original.

Os arquivos originais não são modificados.

Uso:
    python3 scripts/gif_black_bg.py [DIR] [opcoes]

Argumentos:
    DIR                       Diretório com os GIFs (default: assets/gif animadas/)

Opções:
    --size W H                Resolução do canvas alvo (default: 240 240)
    --suffix S                Sufixo aplicado ao nome de saída (default: _black)
    --no-resize               Mantém o tamanho original do GIF (apenas adiciona
                              fundo preto, sem expandir para o canvas alvo)
    --overwrite               Regera mesmo se o arquivo de saída já existir
    -h, --help                Mostra esta ajuda

Exemplos:
    # Default — processa assets/gif animadas/ e gera *_black.gif 240x240
    python3 scripts/gif_black_bg.py

    # Outro diretório
    python3 scripts/gif_black_bg.py ./meus_gifs

    # Canvas customizado (ex.: outro dispositivo)
    python3 scripts/gif_black_bg.py --size 320 320

    # Apenas adiciona fundo preto, sem mudar dimensões
    python3 scripts/gif_black_bg.py --no-resize

    # Sufixo customizado
    python3 scripts/gif_black_bg.py --suffix _bg

Requisitos: Pillow (já instalado como dependência do projeto kraken).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageSequence

DEFAULT_DIR = Path("assets/gif animadas")
DEFAULT_SIZE = (240, 240)  # native LCD resolution of NZXT Kraken 2023 Standard
DEFAULT_SUFFIX = "_black"


def _build_palette_image(rgb_frames: list[Image.Image]) -> Image.Image:
    """Build a 256-color palette image with pure black at index 0.

    Quantizes a sampled image and remaps it so (0,0,0) sits at index 0; needed
    so we can set the GIF's background color index to a real black instead of
    Pillow's default white. Also ensures the per-frame "outside-extent"
    fallback shown by viewers/extractors is black.
    """
    sample = Image.new("RGB", rgb_frames[0].size)
    sample.paste(rgb_frames[0], (0, 0))
    pal_src = sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    raw = pal_src.getpalette() or []
    raw = (raw + [0] * (768 - len(raw)))[:768]
    new_palette = [0, 0, 0] + raw[:765]
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(new_palette)
    return pal_img


def _crush_to_black(rgba: Image.Image, threshold: int) -> Image.Image:
    """Force any pixel with all RGB channels <= threshold to pure (0,0,0).

    Some source GIFs use a near-black background (e.g. (12,4,6)) instead of
    pure black; that creates a visible boundary against our pure-black canvas
    pad on the LCD. Snapping those pixels to pure black makes the merge
    seamless.
    """
    if threshold <= 0:
        return rgba
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                px[x, y] = (0, 0, 0, a)
    return rgba


def fit_centered(frame_rgba: Image.Image, target: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGBA", target, (0, 0, 0, 255))
    w, h = frame_rgba.size
    tw, th = target
    if (w, h) != target:
        scale = min(tw / w, th / h)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        resized = frame_rgba.resize((new_w, new_h), Image.LANCZOS)
    else:
        resized = frame_rgba
    off = ((tw - resized.size[0]) // 2, (th - resized.size[1]) // 2)
    canvas.alpha_composite(resized, dest=off)
    return canvas


def composite_gif(
    src: Path,
    dst: Path,
    target: tuple[int, int] | None,
    *,
    crush_threshold: int = 16,
) -> None:
    with Image.open(src) as im:
        native_size = im.size
        loop = im.info.get("loop", 0)
        canvas_size = target or native_size

        frames_out: list[Image.Image] = []
        durations: list[int] = []
        accum = Image.new("RGBA", native_size, (0, 0, 0, 255))

        for frame in ImageSequence.Iterator(im):
            duration = frame.info.get("duration", 100)
            disposal = getattr(frame, "disposal_method", 0)
            rgba = frame.convert("RGBA")

            if disposal == 2:
                base = Image.new("RGBA", native_size, (0, 0, 0, 255))
                composed_native = Image.alpha_composite(base, rgba)
                accum = Image.new("RGBA", native_size, (0, 0, 0, 255))
                accum.paste(composed_native, (0, 0))
            else:
                composed_native = Image.alpha_composite(accum, rgba)
                accum = composed_native.copy()

            if target is None:
                full = composed_native
            else:
                full = fit_centered(composed_native, target)
            full = _crush_to_black(full, crush_threshold)
            final = full.convert("RGB")
            frames_out.append(final)
            durations.append(duration)

        if not frames_out:
            raise RuntimeError(f"No frames in {src}")

        # Quantize every frame against a shared palette where index 0 = pure
        # black. Combined with background=0 in the GIF header, this makes any
        # area outside a frame's extent (used by Pillow when partial frames
        # are decoded without inter-frame composition, as kraken's
        # extract_frames does via img.seek(i)+convert("RGB")) render as black
        # rather than the default white.
        palette_image = _build_palette_image(frames_out)
        paletted = [
            f.quantize(palette=palette_image, dither=Image.Dither.FLOYDSTEINBERG)
            for f in frames_out
        ]

        paletted[0].save(
            dst,
            save_all=True,
            append_images=paletted[1:],
            duration=durations,
            loop=loop,
            disposal=2,
            optimize=False,
            background=0,
        )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Gera cópias de GIFs com fundo preto para o LCD do Kraken.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("dir", nargs="?", type=Path, default=DEFAULT_DIR,
                   help="Diretório com os GIFs (default: assets/gif animadas/)")
    p.add_argument("--size", nargs=2, type=int, metavar=("W", "H"),
                   default=list(DEFAULT_SIZE),
                   help="Resolução do canvas alvo (default: 240 240)")
    p.add_argument("--suffix", default=DEFAULT_SUFFIX,
                   help="Sufixo aplicado ao nome de saída (default: _black)")
    p.add_argument("--no-resize", action="store_true",
                   help="Mantém tamanho original (não redimensiona para o canvas)")
    p.add_argument("--overwrite", action="store_true",
                   help="Regera mesmo se o arquivo de saída já existir")
    p.add_argument("--crush-threshold", type=int, default=16,
                   help="Pixels com todos os canais RGB <= N viram preto puro "
                        "(default: 16; use 0 para desativar)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    src_dir: Path = args.dir
    if not src_dir.is_dir():
        print(f"erro: diretório não encontrado: {src_dir}", file=sys.stderr)
        return 1

    target = None if args.no_resize else (args.size[0], args.size[1])
    suffix = args.suffix

    gifs = sorted(p for p in src_dir.glob("*.gif") if suffix not in p.stem)
    if not gifs:
        print(f"nenhum GIF encontrado em {src_dir} (excluindo *{suffix}.gif)")
        return 0

    print(f"processando {len(gifs)} GIF(s) em {src_dir}")
    print(f"canvas alvo: {'nativo (sem redimensionar)' if target is None else f'{target[0]}x{target[1]}'}")
    print(f"sufixo: {suffix}")
    print()

    for src in gifs:
        dst = src.with_name(f"{src.stem}{suffix}.gif")
        if dst.exists() and not args.overwrite:
            print(f"  pulado (já existe): {dst.name}")
            continue
        with Image.open(src) as im:
            in_size = im.size
        out_size = in_size if target is None else target
        print(f"  {src.name} ({in_size[0]}x{in_size[1]})  ->  {dst.name} ({out_size[0]}x{out_size[1]})")
        composite_gif(src, dst, target, crush_threshold=args.crush_threshold)

    print("\nconcluído.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
