## declare an array variable
declare -a exts=("wav" "ogg" "flac" "mp3" "mp4")

mkdir -p results

## now loop through the above array
for i in "${exts[@]}"
do
    python benchmark_read.py --ext "$i"
    python benchmark_info.py --ext "$i"
done

python plot.py
