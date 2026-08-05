import argparse
import json

from config.settings import load_settings
from observer.sqlite_store import SQLiteTraceStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", default="")
    parser.add_argument("--trace-id", default="")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    settings = load_settings()
    store = SQLiteTraceStore(settings.observer.sqlite_path)

    if args.trace_id:
        events = store.list_by_trace(args.trace_id, limit=args.limit)
    elif args.session_id:
        events = store.list_by_session(args.session_id, limit=args.limit)
    else:
        raise SystemExit("Please provide --session-id or --trace-id")

    for event in events:
        print(json.dumps(event.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()