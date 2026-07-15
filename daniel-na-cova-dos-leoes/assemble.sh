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
: > build/offsets.txt
total=0

ids=("${(@f)$(tail -n +2 scenes.tsv | awk -F'\t' 'NF && $1 !~ /^#/ {print $1}')}")

for nn in $ids; do
  [[ -f "audio/${nn}.mp3" ]] || { echo "✗ falta audio/${nn}.mp3"; exit 1; }
  [[ -f "clips/${nn}.mp4" ]] || { echo "✗ falta clips/${nn}.mp4"; exit 1; }

  # início desta cena no master (antes de somar seu seg) — usado p/ posicionar SFX
  printf "%s\t%s\n" "$nn" "$total" >> build/offsets.txt

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

# Mix de áudio: narração (dominante) + BGM suave (se houver audio/bgm.mp3) + SFX
# de momentos-chave posicionados por cena. Limitado a <= -4 dB. Ver mix_sfx.py.
bgmargs=()
[[ -f audio/bgm.mp3 ]] && bgmargs=(--bgm audio/bgm.mp3 --bgmvol "$BGMVOL")
python3 ./mix_sfx.py --narr build/narr_full.wav --out build/mix.wav \
  --total "$total" --offsets build/offsets.txt "${bgmargs[@]}" \
  || { echo "✗ mix_sfx falhou"; exit 1; }

OUT="${SLUG}_final.mp4"
ffmpeg -y -i build/video_only.mp4 -i build/mix.wav \
  -filter_complex "[0:v]fade=t=in:st=0:d=0.6,fade=t=out:st=$(echo "$total-1.2" | bc -l):d=1.2[v]" \
  -map "[v]" -map 1:a -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k -shortest \
  "$OUT" -loglevel error

echo "=== PRONTO: $OUT ==="
ffprobe -v error -show_entries format=duration:stream=width,height -of default=noprint_wrappers=1 "$OUT" 2>/dev/null
