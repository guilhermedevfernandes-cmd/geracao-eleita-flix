#!/usr/bin/env python3
"""Montador genérico do PADRÃO OFICIAL do canal (aprovado 12/07/2026, ref. EP03).

Uso: python3 scripts/montar_episodio.py <pasta-do-episodio>
Lê <pasta>/montagem.json:
{
  "final": "EP0X-PREVIEW-....mp4",
  "bgm": "bgm-infantil.mp3",
  "bgm_reflexao": "bgm-reflexao.mp3",
  "cenas": [
    {"nome": "c1", "segs": ["n01"], "planos": ["01-abertura"],
     "pausa": false, "gap": 0.7, "sfx": [["sininhos", 0.8, 0.22]]},
    ...última cena = REFLEXÃO (recebe a trilha própria)...
  ]
}

Padrão: clipes 0.75x · ping-pong em LOOP (sem emenda) p/ cenas longas · fade branco
entre cenas · pausa 2.5s entre cenas · BGM 0.10/0.065 + trilha da reflexão 0.09 ·
alimiter level=0 (pico -4dB) · yuv420p em toda a cadeia · faststart.
"""
import subprocess, json, os, sys, math

EP = os.path.abspath(sys.argv[1])
CFG = json.load(open(os.path.join(EP, "montagem.json"), encoding="utf-8"))
BUILD = os.path.join(EP, "build-v2"); os.makedirs(BUILD, exist_ok=True)

def run(cmd): subprocess.run(cmd, check=True, capture_output=True)
def dur(path):
    out = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration",
                          "-of","csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())

GAP_PADRAO = 0.7
PAUSA = 2.2
RESPIRO = 2.5
INTRO = 2.0
OUTRO = 3.0
SPEED = 0.75
FADE = 0.35

scene_files, scene_durs, sfx_events = [], [], []
t_cursor = INTRO
for cena in CFG["cenas"]:
    nome, segs, planos = cena["nome"], cena["segs"], cena["planos"]
    gap = cena.get("gap", GAP_PADRAO)
    # ---- áudio da cena ----
    inputs, filters, chains = [], [], []
    t = 0.0
    for i, s in enumerate(segs):
        p = os.path.join(EP, "audio", f"{s}.mp3")
        inputs += ["-i", p]
        d = int(t*1000)
        filters.append(f"[{i}:a]aresample=44100,adelay={d}|{d}[a{i}]")
        chains.append(f"[a{i}]")
        t += dur(p) + (gap if i < len(segs)-1 else 0)
    total = t + (PAUSA if cena.get("pausa") else 0) + RESPIRO
    afile = os.path.join(BUILD, f"aud_{nome}.wav")
    fc = ";".join(filters) + f";{''.join(chains)}amix=inputs={len(segs)}:normalize=0,apad=whole_dur={total}[out]"
    run(["ffmpeg","-y",*inputs,"-filter_complex",fc,"-map","[out]","-t",f"{total}",afile])
    # ---- vídeo da cena: planos divididos; ping-pong em LOOP se precisar ----
    per = total / len(planos)
    vparts = []
    for j, pl in enumerate(planos):
        src = os.path.join(EP, "videos", f"{pl}.mp4")
        part = os.path.join(BUILD, f"vid_{nome}_{j}.mp4")
        slow = dur(src)/SPEED
        enc = ["-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p"]
        if per <= slow:
            run(["ffmpeg","-y","-i",src,"-filter_complex",
                 f"[0:v]setpts=PTS/{SPEED},trim=duration={per:.3f},scale=1920:1080:flags=lanczos,fps=30,format=yuv420p[v]",
                 "-map","[v]","-an",*enc,part])
        else:
            # ping-pong (ida+volta) termina onde começa → loop sem emenda
            pp = os.path.join(BUILD, f"pp_{nome}_{j}.mp4")
            run(["ffmpeg","-y","-i",src,"-filter_complex",
                 f"[0:v]setpts=PTS/{SPEED},split[f][r];[r]reverse[rr];[f][rr]concat=n=2:v=1:a=0,"
                 f"scale=1920:1080:flags=lanczos,fps=30,format=yuv420p[v]",
                 "-map","[v]","-an",*enc,pp])
            loops = max(0, math.ceil(per / (2*slow)) - 1)
            run(["ffmpeg","-y","-stream_loop",str(loops),"-i",pp,
                 "-t",f"{per:.3f}","-vf","fps=30,format=yuv420p","-an",*enc,part])
        vparts.append(part)
    lst = os.path.join(BUILD, f"cat_{nome}.txt")
    with open(lst,"w") as f: [f.write(f"file '{p}'\n") for p in vparts]
    vfile = os.path.join(BUILD, f"vid_{nome}.mp4")
    fades = f"fade=t=in:st=0:d={FADE}:color=white,fade=t=out:st={total-FADE:.3f}:d={FADE}:color=white"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-vf",fades,
         "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",vfile])
    scene_files.append((vfile, afile)); scene_durs.append(total)
    for sf, off, vol in cena.get("sfx", []):
        sfx_events.append((os.path.join(EP,"sfx",f"{sf}.mp3"), t_cursor+off, vol))
    t_cursor += total
    print(f"cena {nome}: {total:.1f}s", flush=True)

total_ep = INTRO + sum(scene_durs) + OUTRO
print(f"duração alvo: {total_ep:.1f}s")

white = os.path.join(BUILD,"white.mp4"); white2 = os.path.join(BUILD,"white2.mp4")
for w, d in ((white, INTRO), (white2, OUTRO)):
    run(["ffmpeg","-y","-f","lavfi","-i",f"color=white:s=1920x1080:r=30:d={d}",
         "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",w])
lst = os.path.join(BUILD,"cat_ep.txt")
with open(lst,"w") as f:
    f.write(f"file '{white}'\n")
    for v,_ in scene_files: f.write(f"file '{v}'\n")
    f.write(f"file '{white2}'\n")
vep = os.path.join(BUILD,"video_ep.mp4")
run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
     "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",vep])

# ---- áudio final: narrações + BGM alegre até a reflexão + trilha da reflexão ----
inputs = ["-i", vep]
filters, mixes = [], []
idx = 1; t = INTRO
for _, a in scene_files:
    inputs += ["-i", a]
    d = int(t*1000)
    filters.append(f"[{idx}:a]adelay={d}|{d}[n{idx}]"); mixes.append(f"[n{idx}]")
    t += dur(a); idx += 1
fim = total_ep
t_reflex = INTRO + sum(scene_durs[:-1])
inputs += ["-stream_loop","-1","-i",os.path.join(EP,CFG["bgm"])]
filters.append(
    f"[{idx}:a]aresample=44100,atrim=duration={t_reflex:.3f},"
    f"volume='if(lt(t,{INTRO+scene_durs[0]}),0.10,0.065)':eval=frame,"
    f"afade=t=in:d=1,afade=t=out:st={t_reflex-1.2:.3f}:d=1.2[bgm1]")
mixes.append("[bgm1]"); idx += 1
inputs += ["-stream_loop","-1","-i",os.path.join(EP,CFG["bgm_reflexao"])]
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
final = os.path.join(EP, CFG["final"])
run(["ffmpeg","-y",*inputs,"-filter_complex",fc,"-map","0:v","-map","[aout]",
     "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",final])
print(f"FINAL: {final} ({dur(final):.1f}s)")
