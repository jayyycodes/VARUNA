# LLM Self-Hosting Pipeline — Full Command Reference

Everything from downloading a small model to deploying it as a Docker container, in order.

---

## 1. WSL + CUDA setup (one-time)

```bash
sudo apt update
sudo apt install build-essential cmake git -y

# Check if CUDA toolkit already present
nvcc --version

# If not found, install it:
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda-toolkit-12-6 -y

# Add to PATH (append to ~/.bashrc, then `source ~/.bashrc`)
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

## 2. Build llama.cpp from source

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j 8
```

## 3. Python venv for conversion scripts

```bash
sudo apt install python3.12-venv -y   # if missing

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Download a small model from Hugging Face

```bash
pip install huggingface_hub
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct --local-dir ~/qwen2.5-1.5b-instruct
```

## 5. Convert HF weights → GGUF (f16, unquantized)

```bash
python convert_hf_to_gguf.py ~/qwen2.5-1.5b-instruct --outfile ~/qwen1.5b-f16.gguf --outtype f16
```

## 6. Quantize it yourself

```bash
./build/bin/llama-quantize ~/qwen1.5b-f16.gguf ~/qwen1.5b-q4_k_m.gguf Q4_K_M
```

## 7. Test locally

```bash
./build/bin/llama-cli -m ~/qwen1.5b-q4_k_m.gguf -p "Explain quantization in one sentence" -n 50 -ngl 999
```

---

## 8. Package for RunPod (Cloud phase)

```bash
mkdir ~/runpod-qwen && cd ~/runpod-qwen
cp ~/qwen1.5b-q4_k_m.gguf .
```

### `handler.py`

```python
import runpod
from llama_cpp import Llama

llm = Llama(
    model_path="/qwen1.5b-q4_k_m.gguf",
    n_gpu_layers=999,
    n_ctx=2048,
)

def handler(event):
    prompt = event["input"]["prompt"]
    output = llm(prompt, max_tokens=200)
    return output["choices"][0]["text"]

runpod.serverless.start({"handler": handler})
```

Create it directly from terminal (avoids editor paste issues):

```bash
cat > handler.py << 'EOF'
import runpod
from llama_cpp import Llama

llm = Llama(
    model_path="/qwen1.5b-q4_k_m.gguf",
    n_gpu_layers=999,
    n_ctx=2048,
)

def handler(event):
    prompt = event["input"]["prompt"]
    output = llm(prompt, max_tokens=200)
    return output["choices"][0]["text"]

runpod.serverless.start({"handler": handler})
EOF
```

### `Dockerfile`

Use the **devel** CUDA image — the `runtime` variant lacks `nvcc` and will fail to compile `llama-cpp-python`.

```bash
cat > Dockerfile << 'EOF'
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    build-essential cmake ninja-build git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY qwen1.5b-q4_k_m.gguf /qwen1.5b-q4_k_m.gguf
COPY handler.py .

RUN CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --no-cache-dir
RUN pip install runpod --no-cache-dir

CMD ["python3", "-u", "handler.py"]
EOF
```

## 9. Build, tag, push

```bash
docker build --no-cache -t qwen-summarizer .

docker tag qwen-summarizer jackkk5121/qwen-summarizer:latest
docker login
docker push jackkk5121/qwen-summarizer:latest
```

---

## Notes / gotchas hit along the way

- `pip install` inside WSL system Python fails with `externally-managed-environment` — always use a venv (`python3 -m venv .venv && source .venv/bin/activate`).
- `python3 -m venv` can fail with `ensurepip is not available` — fix: `sudo apt install python3.12-venv -y`.
- Files created via VS Code paste can silently save as empty (0 bytes) — verify with `cat filename` before building. When in doubt, write files directly with `cat > file << 'EOF' ... EOF` from the terminal instead.
- `llama-cpp-python` build needs `ninja-build` + `cmake` + `build-essential` installed **inside the Docker image itself** — the base CUDA image doesn't have them.
- CUDA **runtime** images lack `nvcc`; you need the **devel** variant to compile CUDA code (like `llama-cpp-python` with GPU support) inside Docker.
- Compiling CUDA kernels from source uses CPU, not GPU — 100% CPU / 0% GPU during `pip install llama-cpp-python` is expected, not a problem.
- To speed up future builds, restrict compilation to your actual GPU architecture (RTX 4050 = compute capability 8.9): `CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=89"`.
