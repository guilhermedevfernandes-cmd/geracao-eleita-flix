#!/bin/zsh
# Monta o MP4 final: cada cena dura o tempo da sua narração (vídeo esticado/cortado
# p/ casar), depois mixa narração (alto) + música de fundo opcional (baixo).
# Lê meta.env + scenes.tsv. Requer clips/NN.mp4 e audio/NN.mp3 de cada cena.
# Saída: <SLUG>_final.mp4 · 1920x1080 24fps (16:9) ou 1080x1920 (9:16).
set -eu
cd "${0:A:h}"
source ./meta.env

if [[ "$ASPECT" == "9:16" ]]; then W=1080; H=1920; else W=1920; H=1080; fi
FPS=24
CLIP=${VIDEO_DUR:-${CLIP_SECONDS:-8}}

rm -rf build && mkdir -p build
: > build/concat.txt
: > build/anarr.txt
total=0

ids=("${(@f)$(tail -n +2 scenes.tsv | awk -F'\t' 'NF && $1 !~ /^#/ {print $1}')}")

for nn in $ids; do
  [[ -f "audio/${nn}.mp3" ]] || { echo "✗ falta audio/${nn}.mp3"; exit 1; }
  [[ -f "clips/${nn}.mp4" ]] || { echo "✗ falta clips/${nn}.mp4"; exit 1; }

  nd=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "audio/${nn}.mp3")
  seg=$(echo "$nd + $TAIL" | bc -l)
  total=$(echo "$total + $seg" | bc -l)

  if (( $(echo "$seg > $CLIP" | bc -l) )); then
    factor=$(echo "$seg / $CLIP" | bc -l)   # estica o vídeo p/ cobrir a narração
    vf="setpts=${factor}*PTS,scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,fps=${FPS},setsar=1"
  else
    vf="scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,fps=${FPS},setsar=1"
  fi
  ffmpeg -y -i "clips/${nn}.mp4" -an -vf "$vf" -t "$seg" -c:v libx264 -pix_fmt yuv420p -crf 18 "build/v${nn}.mp4" -loglevel error
  echo "file 'v${nn}.mp4'" >> build/concat.txt

  ffmpeg -y -i "audio/${nn}.mp3" -af "apad" -t "$seg" -ar 44100 -ac 2 "build/a${nn}.wav" -loglevel error
  echo "file 'a${nn}.wav'" >> build/anarr.txt
  printf "  cena %s  narr %.1fs  seg %.1fs\n" "$nn" "$nd" "$seg"
done

printf ">> total: %.1fs\n" "$total"

ffmpeg -y -f concat -safe 0 -i build/concat.txt -c:v libx264 -pix_fmt yuv420p -crf 18 build/video_only.mp4 -loglevel error
ffmpeg -y -f concat -safe 0 -i build/anarr.txt -c:a pcm_s16le build/narr_full.wav -loglevel error

# Mix de áudio: com música de fundo se houver audio/bgm.mp3, senão só narração
if [[ -f audio/bgm.mp3 ]]; then
  ffmpeg -y -stream_loop -1 -i audio/bgm.mp3 -t "$total" -ar 44100 -ac 2 build/bgm_cut.wav -loglevel error
  ffmpeg -y -i build/narr_full.wav -i build/bgm_cut.wav -filter_complex \
    "[0:a]volume=1.0[n];[1:a]volume=${BGMVOL},afade=t=out:st=$(echo "$total-3" | bc -l):d=3[b];[n][b]amix=inputs=2:duration=first:dropout_transition=0[a]" \
    -map "[a]" -ar 44100 -ac 2 build/mix.wav -loglevel error
else
  echo "  (sem audio/bgm.mp3 — montando só com narração)"
  cp build/narr_full.wav build/mix.wav
fi

OUT="${SLUG}_final.mp4"
ffmpeg -y -i build/video_only.mp4 -i build/mix.wav \
  -filter_complex "[0:v]fade=t=in:st=0:d=0.6,fade=t=out:st=$(echo "$total-1.2" | bc -l):d=1.2[v]" \
  -map "[v]" -map 1:a -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k -shortest \
  "$OUT" -loglevel error

echo "=== PRONTO: $OUT ==="
ffprobe -v error -show_entries format=duration:stream=width,height -of default=noprint_wrappers=1 "$OUT" 2>/dev/null
