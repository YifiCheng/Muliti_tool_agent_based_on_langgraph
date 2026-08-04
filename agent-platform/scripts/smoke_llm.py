import argparse

from config.settings import load_settings
from llm.client import build_llm_client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="用一句话说明 LangGraph 适合做什么。")
    args = parser.parse_args()

    settings = load_settings()
    client = build_llm_client(settings)
    result = client.chat([{"role": "user", "content": args.prompt}])
    print(result)


if __name__ == "__main__":
    main()