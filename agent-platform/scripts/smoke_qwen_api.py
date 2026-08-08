import argparse
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from llm.client import build_llm_client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt",
        default="用一句话说明企业知识库 Agent 的作用。",
    )
    args = parser.parse_args()

    settings = load_settings()
    settings.llm.provider = "qwen_api"

    started = perf_counter()
    client = build_llm_client(settings)
    answer = client.chat(
        [{"role": "user", "content": args.prompt}],
        temperature=0.2,
    )
    latency_ms = int((perf_counter() - started) * 1000)

    print("provider=qwen_api")
    print(f"model={getattr(client.provider, 'model', '')}")
    print(f"base_url={getattr(client.provider, 'base_url', '')}")
    print(f"latency_ms={latency_ms}")
    print(f"answer={answer}")

    if not answer.strip():
        raise RuntimeError("qwen_api returned empty answer")

    print("smoke_qwen_api=ready")


if __name__ == "__main__":
    main()