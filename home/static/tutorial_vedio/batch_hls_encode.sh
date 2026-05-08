





SRC_DIR="/path/to/example/home/static/tutorial_vedio"
CRF=24
FPS=30
SEG=10
RES_LIST=("1280x720" "854x480")



find "$SRC_DIR" -type f -iname "*.mp4" | while read -r FILE; do
  DIR=$(dirname "$FILE")
  BASE=$(basename "$FILE" .mp4)
  OUT_DIR="$DIR/${BASE}_hls"
  mkdir -p "$OUT_DIR"


  for RES in "${RES_LIST[@]}"; do
    OUT_NAME="${RES//x/}k"

    ffmpeg -y -i "$FILE" \
      -vf "scale=${RES}:force_original_aspect_ratio=decrease" \
      -c:v libx264 -profile:v main -level 4.0 -preset veryfast \
      -crf $CRF -r $FPS -pix_fmt yuv420p \
      -c:a aac -b:a 96k -ac 2 \
      -movflags +faststart \
      -hls_time $SEG -hls_playlist_type vod \
      -hls_segment_filename "$OUT_DIR/${OUT_NAME}_%03d.ts" \
      "$OUT_DIR/${OUT_NAME}.m3u8"
  done


  {
    echo "
    echo "
    for RES in "${RES_LIST[@]}"; do
      OUT_NAME="${RES//x/}k"
      BW=$( [ "$RES" == "1280x720" ] && echo 2500000 || echo 800000 )
      echo "
      echo "${OUT_NAME}.m3u8"
    done
  } > "$OUT_DIR/master.m3u8"

  echo "✅ 处理完成：$FILE → $OUT_DIR/master.m3u8"
done