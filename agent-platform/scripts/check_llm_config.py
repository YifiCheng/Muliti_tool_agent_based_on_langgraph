import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import load_settings
from llm.client import build_llm_client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=["mock", "qwen_api", "remote_qwen"],
        required=True,
    )
    args = parser.parse_args()

    settings = load_settings()
    settings.llm.provider = args.provider
    client = build_llm_client(settings)
    provider = client.provider

    print(f"provider={args.provider}")
    print(f"class={type(provider).__name__}")
    print(f"model={getattr(provider, 'model', 'not-required')}")
    print(f"base_url={getattr(provider, 'base_url', 'not-required')}")
    print("network_request=not_sent")


if __name__ == "__main__":
    main()