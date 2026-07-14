#!/bin/zsh
# Monta o MP4 final: cada cena dura o tempo da sua narração (vídeo esticado/cortado p/ casar),
# depois mixa narração (alto) + música de fundo (baixo). Saída 1920x1080 24fps.
set -eu
cd "$(dirname "$0")"
W=1920; H=1080; FPS=24
TAIL=0.5            # respiro após cada narração
BGMVOL=0.16
rm -rf build && mkdir -p build
SCENES=(01 02 03 04 05 06 07 08 09 10 11 12 13 13b 14 15 16)

total=0
: > build/concat.txt
: > build/anarr.txt

for nn in $SCENES; do
  nd=$(ffprobe -v error -show_entries format=duration -of csv=p=0 audio/${nn}.mp3)
  seg=$(echo "$nd + $TAIL" | bc -l)
  total=$(echo "$total + $seg" | bc -l)

  # vídeo: escala p/ 1080p (sem distorção) e ajusta duração ao seg
  factor=$(echo "$seg / 8.0" | bc -l)   # >1 estica, <1 corta (via -t)
  if (( $(echo "$seg > 8.0" | bc -l) )); then
    vf="setpts=${factor}*PTS,scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,fps=${FPS},setsar=1"
    ffmpeg -y -i clips/${nn}.mp4 -an -vf "$vf" -t "$seg" -c:v libx264 -pix_fmt yuv420p -crf 18 build/v${nn}.mp4 -loglevel error
  else
    vf="scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2,fps=${FPS},setsar=1"
    ffmpeg -y -i clips/${nn}.mp4 -an -vf "$vf" -t "$seg" -c:v libx264 -pix_fmt yuv420p -crf 18 build/v${nn}.mp4 -loglevel error
  fi
  echo "file 'v${nn}.mp4'" >> build/concat.txt

  # áudio narração: padded com silêncio até seg
  ffmpeg -y -i audio/${nn}.mp3 -af "apad" -t "$seg" -ar 44100 -ac 2 build/a${nn}.wav -loglevel error
  echo "file 'a${nn}.wav'" >> build/anarr.txt
  printf "  cena %s  narr %.1fs  seg %.1fs\n" $nn $nd $seg
done

printf ">> total: %.1fs\n" $total

# concat vídeo
ffmpeg -y -f concat -safe 0 -i build/concat.txt -c:v libx264 -pix_fmt yuv420p -crf 18 build/video_only.mp4 -loglevel error
# concat narração
ffmpeg -y -f concat -safe 0 -i build/anarr.txt -c:a pcm_s16le build/narr_full.wav -loglevel error

# bgm: loop/trim ao total
ffmpeg -y -stream_loop -1 -i audio/bgm.mp3 -t "$total" -ar 44100 -ac 2 build/bgm_cut.wav -loglevel error

# mix narração + bgm com fade out final
ffmpeg -y -i build/narr_full.wav -i build/bgm_cut.wav -filter_complex \
  "[0:a]volume=1.0[n];[1:a]volume=${BGMVOL},afade=t=out:st=$(echo "$total-3" | bc -l):d=3[b];[n][b]amix=inputs=2:duration=first:dropout_transition=0[a]" \
  -map "[a]" -ar 44100 -ac 2 build/mix.wav -loglevel error

# mux final + fade preto no fim
ffmpeg -y -i build/video_only.mp4 -i build/mix.wav \
  -filter_complex "[0:v]fade=t=in:st=0:d=0.6,fade=t=out:st=$(echo "$total-1.2" | bc -l):d=1.2[v]" \
  -map "[v]" -map 1:a -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k -shortest \
  "DAVI_E_GOLIAS_final.mp4" -loglevel error

echo "=== PRONTO: DAVI_E_GOLIAS_final.mp4 ==="
ffprobe -v error -show_entries format=duration:stream=width,height -of default=noprint_wrappers=1 DAVI_E_GOLIAS_final.mp4 2>/dev/null
