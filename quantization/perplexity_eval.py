import math
import argparse
import requests
from tqdm import tqdm
from datasets import load_dataset
from transformers import AutoTokenizer


def call_vllm_logprobs(base_url: str, api_key: str, model: str, prompt: str, max_tokens: int = 1):
    """
    调用 vLLM OpenAI-compatible /v1/completions，返回 choices[0].logprobs.token_logprobs 等字段
    """
    url = base_url.rstrip("/") + "/v1/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,      # 通常设 1 即可；我们只关心 prompt 的 logprobs
        "temperature": 0,
        "echo": True,                  # 关键：回显 prompt 的 token/logprobs
        "logprobs": 0,                 # 关键：返回所选 token 的 logprob（不需要 top-k）
        "stream": False,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=300)
    r.raise_for_status()
    return r.json()


def iter_texts(dataset_name: str, subset: str, split: str, field: str, max_samples: int):
    ds = load_dataset(dataset_name, subset, split=split) if subset else load_dataset(dataset_name, split=split)
    n = 0
    for ex in ds:
        txt = ex.get(field, "")
        if not isinstance(txt, str):
            continue
        txt = txt.strip()
        if not txt:
            continue
        yield txt
        n += 1
        if max_samples and n >= max_samples:
            break


def compute_ppl_via_server(
    base_url: str,
    api_key: str,
    model: str,
    tokenizer_name: str,
    dataset_name: str,
    subset: str,
    split: str,
    field: str,
    max_samples: int,
    max_length: int,
    stride: int,
):
    """
    滑动窗口 PPL：
    - 用 HF tokenizer 把文本切成 token ids
    - 每个窗口 decode 成 prompt 文本送给 vLLM
    - 用返回的 prompt token_logprobs 计算 NLL
    """
    tok = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True, trust_remote_code=True)

    total_nll = 0.0
    total_tokens = 0

    for text in tqdm(iter_texts(dataset_name, subset, split, field, max_samples), desc=f"PPL on {dataset_name}:{split}"):
        ids = tok.encode(text, add_special_tokens=False)
        if len(ids) < 2:
            continue

        # 滑动窗口
        start = 0
        while start < len(ids) - 1:
            end = min(start + max_length, len(ids))
            window_ids = ids[start:end]
            if len(window_ids) < 2:
                break

            # 解码成 prompt（尽量保证与模型 tokenizer 一致）
            prompt = tok.decode(window_ids, clean_up_tokenization_spaces=False)

            resp = call_vllm_logprobs(base_url, api_key, model, prompt, max_tokens=1)
            choice = resp["choices"][0]
            lp = choice["logprobs"]["token_logprobs"]
            tokens = choice["logprobs"]["tokens"]

            # echo=true 时，token_logprobs 对应 prompt+生成；我们只取前 len(window_ids) 个 prompt token
            prompt_len = len(window_ids)
            lp = lp[:prompt_len]
            tokens = tokens[:prompt_len]

            # 第一个 token 通常没有条件概率（可能是 None），从第 2 个 token 开始累计 NLL
            for i in range(1, len(lp)):
                if lp[i] is None:
                    continue
                total_nll += -float(lp[i])
                total_tokens += 1

            if end == len(ids):
                break
            start += stride

    ppl = math.exp(total_nll / max(total_tokens, 1))
    return ppl, total_tokens


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_url", type=str, default="http://127.0.0.1:8000")
    ap.add_argument("--api_key", type=str, default="")
    ap.add_argument("--model", type=str, required=True, help="vLLM serve 时的 model 名称")
    ap.add_argument("--tokenizer", type=str, default=None, help="HF tokenizer 名称/路径；默认用 --model")
    ap.add_argument("--dataset", type=str, default="wikitext")
    ap.add_argument("--subset", type=str, default="wikitext-2-raw-v1")
    ap.add_argument("--split", type=str, default="test")
    ap.add_argument("--field", type=str, default="text")
    ap.add_argument("--max_samples", type=int, default=200, help="c4 很大，建议限制样本数")
    ap.add_argument("--max_length", type=int, default=1024, help="滑窗窗口 token 数")
    ap.add_argument("--stride", type=int, default=512, help="滑窗步长")
    args = ap.parse_args()

    tokenizer_name = args.tokenizer or args.model
    ppl, ntok = compute_ppl_via_server(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        tokenizer_name=tokenizer_name,
        dataset_name=args.dataset,
        subset=args.subset,
        split=args.split,
        field=args.field,
        max_samples=args.max_samples,
        max_length=args.max_length,
        stride=args.stride,
    )
    print(f"PPL={ppl:.4f}  (tokens={ntok})")


if __name__ == "__main__":
    main()
