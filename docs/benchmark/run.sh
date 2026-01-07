## declare an array variable
declare -a exts=("wav" "ogg" "flac" "mp3" "mp4")

mkdir -p results

if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

## now loop through the above array
for i in "${exts[@]}"
do
    uv run --python 3.12 benchmark_read.py --ext "$i"
    uv run --python 3.12 benchmark_info.py --ext "$i"
done

uv run --python 3.12 plot.py
