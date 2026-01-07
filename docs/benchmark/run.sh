PYTHON_VERSION="3.12"

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
    uv run --python $PYTHON_VERSION benchmark_read.py --ext "$i"
    uv run --python $PYTHON_VERSION benchmark_info.py --ext "$i"
done

uv run --python $PYTHON_VERSION plot.py
