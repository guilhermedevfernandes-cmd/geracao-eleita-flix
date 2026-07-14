#!/usr/bin/env python3
"""Montagem do EP04 — Caim e Abel (padrão EP03: multi-plano, cortes secos na cena,
fade branco entre cenas, BGM 0.10/0.065/0.08, reflexão com bgm própria, clipes 0.75x)."""
import subprocess, os

EP = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(EP, "build"); os.makedirs(BUILD, exist_ok=True)
def run(cmd): subprocess.run(cmd, check=True, capture_output=True)
def dur(path):
    out = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
                          "-of","csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())

GAP = 0.7
PAUSA = 2.2
RESPIRO = 2.5
INTRO = 2.0
OUTRO = 3.0
SPEED = 0.75
FADE = 0.35

# v2 (13/07/2026, feedback do usuário): 2 sonhos (c3p2b), poço + mentira a Jacó
# (c4pA/B/C), túnica masculina, SEM sininhos/twinkle (som de "chocalho").
CENAS = [
    ("c1", ["c1_0"], ["c1p1","c1p2"], False, []),
    ("c2", ["c2_0"], ["c2p1","c2p2","c2p3"], False, [("tcham-presente",6.5,0.28)]),
    ("c3", ["c3_0"], ["c3p1","c3p2","c3p2b","c3p3"], False, []),
    ("c4", ["c4_0"], ["c4pA","c4pB","c4pC","c4p1","c4p3"], False, [("vento-triste",8,0.20)]),
    ("c5", ["c5_0"], ["c5p1","c5p2","c5p3"], False, [("harpa-v2",1.0,0.18),("tcham-presente",15,0.25)]),
    ("c6", ["c6_0"], ["c6p1","c6p2","c6p3"], False, [("harpa-v2",14,0.18)]),
    ("c7", ["c7_0"], ["c7p1","c7p2","c7p3"], False, []),
    ("c10", ["c10_full"], ["c2p3","c5p1","c6p3","c7p2","c1p1"], False, []),
]

scene_files, scene_durs, sfx_events = [], [], []
t_cursor = INTRO
for nome, segs, planos, pausa, sfxs in CENAS:
    gap_scene = 1.3 if nome == "c10" else GAP
    inputs, filters, chains = [], [], []
    t = 0.0
    for i, s in enumerate(segs):
        p = os.path.join(EP, "audio", f"{s}.mp3")
        inputs += ["-i", p]
        delay_ms = int(t*1000)
        filters.append(f"[{i}:a]aresample=44100,adelay={delay_ms}|{delay_ms}[a{i}]")
        chains.append(f"[a{i}]")
        t += dur(p) + (gap_scene if i < len(segs)-1 else 0)
    total = t + (PAUSA if pausa else 0) + RESPIRO
    afile = os.path.join(BUILD, f"aud_{nome}.wav")
    fc = ";".join(filters) + f";{''.join(chains)}amix=inputs={len(segs)}:normalize=0,apad=whole_dur={total}[out]"
    run(["ffmpeg","-y",*inputs,"-filter_complex",fc,"-map","[out]","-t",f"{total}",afile])
    per = total / len(planos)
    vparts = []
    for j, pl in enumerate(planos):
        src = os.path.join(EP, "videos", f"{pl}.mp4")
        part = os.path.join(BUILD, f"vid_{nome}_{j}.mp4")
        slow = dur(src)/SPEED
        if per <= slow:
            vf = f"setpts=PTS/{SPEED},trim=duration={per:.3f}"
        else:
            vf = (f"setpts=PTS/{SPEED},split[f][r];[r]reverse[rr];[f][rr]concat=n=2:v=1:a=0,"
                  f"trim=duration={per:.3f}")
        run(["ffmpeg","-y","-i",src,"-filter_complex",f"[0:v]{vf},scale=1920:1080:flags=lanczos,fps=30,format=yuv420p[v]",
             "-map","[v]","-an","-c:v","libx264","-preset","fast","-crf","18",part])
        vparts.append(part)
    lst = os.path.join(BUILD, f"cat_{nome}.txt")
    with open(lst,"w") as f: [f.write(f"file '{p}'\n") for p in vparts]
    vfile = os.path.join(BUILD, f"vid_{nome}.mp4")
    fades = f"fade=t=in:st=0:d={FADE}:color=white,fade=t=out:st={total-FADE:.3f}:d={FADE}:color=white"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-vf",fades,
         "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",vfile])
    scene_files.append((vfile, afile)); scene_durs.append(total)
    for sf, off, vol in sfxs: sfx_events.append((os.path.join(EP,"sfx",f"{sf}.mp3"), t_cursor+off, vol))
    t_cursor += total
    print(f"cena {nome}: {total:.1f}s", flush=True)

total_ep = INTRO + sum(scene_durs) + OUTRO
print(f"duração alvo: {total_ep:.1f}s")

white = os.path.join(BUILD,"white.mp4")
run(["ffmpeg","-y","-f","lavfi","-i",f"color=white:s=1920x1080:r=30:d={INTRO}",
     "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",white])
white2 = os.path.join(BUILD,"white2.mp4")
run(["ffmpeg","-y","-f","lavfi","-i",f"color=white:s=1920x1080:r=30:d={OUTRO}",
     "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",white2])
lst = os.path.join(BUILD,"cat_ep.txt")
with open(lst,"w") as f:
    f.write(f"file '{white}'\n")
    for v,_ in scene_files: f.write(f"file '{v}'\n")
    f.write(f"file '{white2}'\n")
vep = os.path.join(BUILD,"video_ep.mp4")
run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
     "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",vep])

inputs = ["-i", vep]
filters, mixes = [], []
idx = 1
t = INTRO
for _, a in scene_files:
    inputs += ["-i", a]
    d = int(t*1000)
    filters.append(f"[{idx}:a]adelay={d}|{d}[n{idx}]"); mixes.append(f"[n{idx}]")
    t += dur(a); idx += 1
fim = total_ep
t_reflex = INTRO + sum(scene_durs[:-1])
bgm = os.path.join(EP,"bgm-infantil.mp3")
inputs += ["-stream_loop","-1","-i",bgm]
filters.append(
    f"[{idx}:a]aresample=44100,atrim=duration={t_reflex:.3f},"
    f"volume='if(lt(t,{INTRO+scene_durs[0]}),0.10,0.065)':eval=frame,"
    f"afade=t=in:d=1,afade=t=out:st={t_reflex-1.2:.3f}:d=1.2[bgm1]")
mixes.append("[bgm1]"); idx += 1
bgm2 = os.path.join(EP,"bgm-reflexao.mp3")
inputs += ["-stream_loop","-1","-i",bgm2]
d2 = int(t_reflex*1000)
filters.append(
    f"[{idx}:a]aresample=44100,atrim=duration={fim-t_reflex:.3f},volume=0.09,"
    f"afade=t=in:d=1,afade=t=out:st={fim-t_reflex-2:.3f}:d=2,adelay={d2}|{d2}[bgm2]")
mixes.append("[bgm2]"); idx += 1
for sf, off, vol in sfx_events:
    inputs += ["-i", sf]
    d = int(off*1000)
    filters.append(f"[{idx}:a]volume={vol},adelay={d}|{d}[s{idx}]"); mixes.append(f"[s{idx}]")
    idx += 1
fc = ";".join(filters) + f";{''.join(mixes)}amix=inputs={len(mixes)}:normalize=0,alimiter=limit=0.63:level=0[aout]"
final = os.path.join(EP,"EP06-PREVIEW-JOSE-E-A-TUNICA-COLORIDA.mp4")
run(["ffmpeg","-y",*inputs,"-filter_complex",fc,"-map","0:v","-map","[aout]",
     "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",final])
print(f"FINAL: {final} ({dur(final):.1f}s)")
