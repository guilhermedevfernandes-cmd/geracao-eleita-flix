#!/usr/bin/env python3
"""Mixa o áudio final do episódio: narração (dominante) + BGM (suave, em loop com
fade-out) + SFX de momentos-chave posicionados no offset de cada cena. Limita o
pico a <= -4 dB (regra do canal). Chamado por assemble.sh.

Uso:
  mix_sfx.py --narr build/narr_full.wav --out build/mix.wav --total 195.3 \
             --offsets build/offsets.txt [--bgm audio/bgm.mp3 --bgmvol 0.10]

offsets.txt: linhas "NN<TAB>start_seconds" (início de cada cena no master).
O mapa de SFX (cena -> arquivo, volume) é fixo abaixo — só momentos-chave.
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

# Momentos-chave (cena -> (arquivo em sfx/, volume)). Níveis baixos: o usuário é
# sensível a áudio alto; narração sempre dominante.
SFX_MAP = {
    "01": ("sfx/amb-campo.mp3",   0.13),  # ambiência pastoral (abertura)
    "05": ("sfx/luz-sonho.mp3",   0.16),  # brilho do sonho (sol, lua e estrelas)
    "12": ("sfx/caravana.mp3",    0.16),  # caravana no deserto rumo ao Egito
    "20": ("sfx/corte-egito.mp3", 0.20),  # corte do Egito (José governador)
}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--narr", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--total", required=True, type=float)
    ap.add_argument("--offsets", required=True)
    ap.add_argument("--bgm", default=None)
    ap.add_argument("--bgmvol", default=0.10, type=float)
    a = ap.parse_args()

    root = Path(__file__).resolve().parent
    starts: dict[str, float] = {}
    for line in Path(a.offsets).read_text().splitlines():
        if not line.strip():
            continue
        nn, st = line.split("\t")
        starts[nn] = float(st)

    total = a.total
    inputs: list[str] = ["-i", a.narr]
    filt: list[str] = ["[0:a]aresample=44100,pan=stereo|c0=c0|c1=c0,volume=1.0[n]"]
    mix_labels = ["[n]"]
    idx = 1

    if a.bgm and Path(root / a.bgm).exists():
        inputs += ["-stream_loop", "-1", "-i", str(root / a.bgm)]
        fade_st = max(0.1, total - 3)
        filt.append(
            f"[{idx}:a]aresample=44100,atrim=0:{total:.3f},"
            f"volume={a.bgmvol},afade=t=out:st={fade_st:.3f}:d=3[b]"
        )
        mix_labels.append("[b]")
        idx += 1

    for nn, (rel, vol) in sorted(SFX_MAP.items()):
        p = root / rel
        if nn not in starts or not p.exists():
            print(f"  (SFX cena {nn}: pulado — sem offset ou arquivo)", file=sys.stderr)
            continue
        ms = int(starts[nn] * 1000)
        inputs += ["-i", str(p)]
        filt.append(
            f"[{idx}:a]aresample=44100,pan=stereo|c0=c0|c1=c0,"
            f"adelay={ms}|{ms},volume={vol}[s{idx}]"
        )
        mix_labels.append(f"[s{idx}]")
        idx += 1

    # amix normalize=0 (mantém níveis); duration=first (comprimento da narração);
    # alimiter limit=0.63 (~ -4 dB) com level=0 (não re-normaliza).
    filt.append(
        "".join(mix_labels) +
        f"amix=inputs={len(mix_labels)}:normalize=0:duration=first[mx];"
        "[mx]alimiter=limit=0.55:level=0[a]"
    )

    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filt),
           "-map", "[a]", "-ar", "44100", "-ac", "2", a.out, "-loglevel", "error"]
    print("  mix_sfx: " + " ".join(f"'{c}'" if " " in c else c for c in cmd[:1]) +
          f" ({len(mix_labels)} camadas de áudio)")
    r = subprocess.run(cmd)
    return r.returncode

if __name__ == "__main__":
    raise SystemExit(main())
