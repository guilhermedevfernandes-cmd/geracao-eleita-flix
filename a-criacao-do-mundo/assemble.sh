#!/bin/zsh
# Montagem master: vídeo sem slow motion excessivo + diálogo normalizado + SFX + BGM com ducking.
source "${0:A:h}/_lib.sh"

require_command ffmpeg
require_command ffprobe
validate_stage assembly

if [[ "$ASPECT" == "9:16" ]]; then
  W=1080
  H=1920
else
  W=1920
  H=1080
fi

rm -rf build
mkdir -p build
SOURCE_LOCK="build/source-lock.json"
python3 "$PIPELINE" assembly-lock \
  --episode "$EPISODE_DIR" \
  --path "$EPISODE_DIR/$SOURCE_LOCK" >/dev/null
prepare_rows scenes SCENE_ROWS
: > build/video-concat.txt
: > build/dialogue-concat.txt
: > build/sfx-concat.txt
: > build/timeline.tsv
print -r -- $'scene\tseconds\tvoice\ttransition' >> build/timeline.tsv

total=0
previous_transition="cut"

while IFS=$'\t' read -r id act shot refs voice text hold image_prompt motion_prompt vfx sfx transition; do
  [[ -z "$id" ]] && continue

  clip="clips/${id}.mp4"
  seg=$(python3 "$PIPELINE" duration \
    --episode "$EPISODE_DIR" --scene "$id" --actual)
  clip_duration=$(ffprobe -v error -select_streams v:0 \
    -show_entries stream=duration \
    -of default=noprint_wrappers=1:nokey=1 "$clip")
  if [[ -z "$clip_duration" || "$clip_duration" == "N/A" ]]; then
    clip_duration=$(ffprobe -v error -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 "$clip")
  fi
  factor=$(python3 -c \
    'import sys; print("{:.8f}".format(float(sys.argv[1]) / float(sys.argv[2])))' \
    "$seg" "$clip_duration")
  stretch=$(python3 -c \
    'import sys; print(1 if float(sys.argv[1]) > 1.0001 else 0)' "$factor")

  vf="scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},fps=${FPS},setsar=1"
  if (( stretch )); then
    vf="setpts=${factor}*PTS,${vf}"
  fi
  case "$previous_transition" in
    dip-to-black) vf="${vf},fade=t=in:st=0:d=0.18:color=black" ;;
    light-flash) vf="${vf},fade=t=in:st=0:d=0.12:color=white" ;;
  esac
  transition_start=$(python3 -c \
    'import sys; print("{:.3f}".format(max(float(sys.argv[1]) - float(sys.argv[2]), 0)))' \
    "$seg" "0.18")
  case "$transition" in
    dip-to-black) vf="${vf},fade=t=out:st=${transition_start}:d=0.18:color=black" ;;
    light-flash)
      flash_start=$(python3 -c \
        'import sys; print("{:.3f}".format(max(float(sys.argv[1]) - 0.12, 0)))' "$seg")
      vf="${vf},fade=t=out:st=${flash_start}:d=0.12:color=white"
      ;;
  esac

  ffmpeg -nostdin -y -i "$clip" -an -vf "$vf" -t "$seg" \
    -c:v libx264 -preset veryfast -crf 17 -pix_fmt yuv420p \
    "build/video-${id}.mp4" -loglevel error
  print -r -- "file 'video-${id}.mp4'" >> build/video-concat.txt

  if [[ "$voice" == "-" ]]; then
    ffmpeg -nostdin -y -f lavfi -i "anullsrc=r=48000:cl=stereo" -t "$seg" \
      -c:a pcm_s24le "build/dialogue-${id}.wav" -loglevel error
  else
    ffmpeg -nostdin -y -i "audio/${id}.mp3" \
      -af "highpass=f=70,lowpass=f=15500,dynaudnorm=f=150:g=11:p=0.92,apad" \
      -t "$seg" -ar 48000 -ac 2 -c:a pcm_s24le \
      "build/dialogue-${id}.wav" -loglevel error
  fi
  print -r -- "file 'dialogue-${id}.wav'" >> build/dialogue-concat.txt

  fade_out=$(python3 -c \
    'import sys; print("{:.3f}".format(max(float(sys.argv[1]) - 0.12, 0)))' "$seg")
  if [[ "$sfx" != "-" && -s "audio/sfx/${id}.wav" ]]; then
    ffmpeg -nostdin -y -stream_loop -1 -i "audio/sfx/${id}.wav" \
      -af "afade=t=in:st=0:d=0.08,afade=t=out:st=${fade_out}:d=0.12,apad" \
      -t "$seg" -ar 48000 -ac 2 -c:a pcm_s24le \
      "build/sfx-${id}.wav" -loglevel error
  else
    ffmpeg -nostdin -y -f lavfi -i "anullsrc=r=48000:cl=stereo" -t "$seg" \
      -c:a pcm_s24le "build/sfx-${id}.wav" -loglevel error
  fi
  print -r -- "file 'sfx-${id}.wav'" >> build/sfx-concat.txt

  total=$(python3 -c \
    'import sys; print("{:.6f}".format(float(sys.argv[1]) + float(sys.argv[2])))' \
    "$total" "$seg")
  printf "%s\t%.3f\t%s\t%s\n" "$id" "$seg" "$voice" "$transition" \
    >> build/timeline.tsv
  printf "  cena %s · %5.2fs · %-12s · stretch %sx\n" \
    "$id" "$seg" "$voice" "$factor"
  previous_transition="$transition"
done < "$SCENE_ROWS"

echo "TIMELINE: ${total}s"

ffmpeg -nostdin -y -f concat -safe 0 -i build/video-concat.txt \
  -c copy build/video-only.mp4 -loglevel error
ffmpeg -nostdin -y -f concat -safe 0 -i build/dialogue-concat.txt \
  -c:a pcm_s24le build/dialogue-full.wav -loglevel error
ffmpeg -nostdin -y -f concat -safe 0 -i build/sfx-concat.txt \
  -c:a pcm_s24le build/sfx-full.wav -loglevel error

if [[ -s audio/bgm.mp3 ]]; then
  music_fade=$(python3 -c \
    'import sys; print("{:.3f}".format(max(float(sys.argv[1]) - 3, 0)))' "$total")
  ffmpeg -nostdin -y -stream_loop -1 -i audio/bgm.mp3 \
    -af "volume=${BGMVOL},afade=t=in:st=0:d=1.5,afade=t=out:st=${music_fade}:d=3,apad" \
    -t "$total" -ar 48000 -ac 2 -c:a pcm_s24le \
    build/bgm-full.wav -loglevel error

  ffmpeg -nostdin -y \
    -i build/dialogue-full.wav \
    -i build/bgm-full.wav \
    -i build/sfx-full.wav \
    -filter_complex \
    "[0:a]volume=1.0,asplit=2[dialogue_mix][dialogue_key]; \
     [1:a][dialogue_key]sidechaincompress=threshold=0.025:ratio=10:attack=15:release=500[ducked]; \
     [2:a]volume=${SFXVOL}[effects]; \
     [dialogue_mix][ducked][effects]amix=inputs=3:duration=first:normalize=0, \
     loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=${MASTER_LIMIT}[master]" \
    -map "[master]" -ar 48000 -ac 2 -c:a pcm_s24le \
    build/master-audio.wav -loglevel error
else
  echo "AVISO: audio/bgm.mp3 ausente; master terá diálogo + SFX."
  ffmpeg -nostdin -y \
    -i build/dialogue-full.wav \
    -i build/sfx-full.wav \
    -filter_complex \
    "[0:a]volume=1.0[dialogue]; \
     [1:a]volume=${SFXVOL}[effects]; \
     [dialogue][effects]amix=inputs=2:duration=first:normalize=0, \
     loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=${MASTER_LIMIT}[master]" \
    -map "[master]" -ar 48000 -ac 2 -c:a pcm_s24le \
    build/master-audio.wav -loglevel error
fi

fade_out=$(python3 -c \
  'import sys; print("{:.3f}".format(max(float(sys.argv[1]) - 1.2, 0)))' "$total")
OUT="${SLUG}_final.mp4"
MASTER_TMP=".${SLUG}_final.$$.mp4"
PIPELINE_TEMP_FILES+=("$EPISODE_DIR/$MASTER_TMP")
PIPELINE_TEMP_FILES+=("$EPISODE_DIR/$MASTER_TMP.meta.json")
SESSION="build/assembly-session.json"
session_fingerprint=$(python3 "$PIPELINE" assembly-session \
  --episode "$EPISODE_DIR" \
  --source-lock "$EPISODE_DIR/$SOURCE_LOCK" \
  --session "$EPISODE_DIR/$SESSION" \
  --timeline "$EPISODE_DIR/build/timeline.tsv" \
  --video "$EPISODE_DIR/build/video-only.mp4" \
  --audio "$EPISODE_DIR/build/master-audio.wav" \
  --output "$EPISODE_DIR/$MASTER_TMP")
ffmpeg -nostdin -y \
  -i build/video-only.mp4 \
  -i build/master-audio.wav \
  -filter_complex \
  "[0:v]fade=t=in:st=0:d=0.5,fade=t=out:st=${fade_out}:d=1.2[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -preset veryfast -crf 17 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -movflags +faststart -shortest \
  -metadata "comment=geflix-session:${session_fingerprint}" \
  "$MASTER_TMP" -loglevel error

python3 "$PIPELINE" master \
  --episode "$EPISODE_DIR" \
  --path "$EPISODE_DIR/$MASTER_TMP" \
  --technical-only \
  --json > build/quality-preflight.json

python3 "$PIPELINE" master \
  --episode "$EPISODE_DIR" \
  --path "$EPISODE_DIR/$MASTER_TMP" \
  --record \
  --session "$EPISODE_DIR/$SESSION" \
  --json > build/quality-precommit.json

python3 "$PIPELINE" commit-master \
  --episode "$EPISODE_DIR" \
  --source "$EPISODE_DIR/$MASTER_TMP" \
  --destination "$EPISODE_DIR/$OUT"

python3 "$PIPELINE" master \
  --episode "$EPISODE_DIR" \
  --path "$EPISODE_DIR/$OUT" \
  --json > build/quality-report.json

echo "MASTER: $EPISODE_DIR/$OUT"
echo "RELATÓRIO: $EPISODE_DIR/build/quality-report.json"
