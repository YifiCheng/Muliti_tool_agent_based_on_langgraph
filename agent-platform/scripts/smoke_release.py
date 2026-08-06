import subprocess
import sys
from pathlib import Path
from uuid import uuid4


def build_commands() -> list[list[str]]:
    run_id = uuid4().hex[:8]
    return [
        [sys.executable, "scripts/init_sqlite.py"],
        [
            sys.executable,
            "scripts/smoke_graph.py",
            "--query",
            "报销超过 5000 元需要谁审批？",
            "--session-id",
            f"release-graph-session-{run_id}",
            "--trace-id",
            f"release-graph-trace-{run_id}",
        ],
        [sys.executable, "scripts/smoke_sql.py", "--query", "销售额最高的商品是什么？"],
        [
            sys.executable,
            "scripts/smoke_approval.py",
            "--decision",
            "approve",
            "--session-id",
            f"release-approval-session-{run_id}",
            "--trace-id",
            f"release-approval-trace-{run_id}",
            "--thread-id",
            f"release-approval-thread-{run_id}",
        ],
        [sys.executable, "scripts/smoke_api.py"],
        [sys.executable, "scripts/smoke_frontend.py"],
    ]


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    for command in build_commands():
        print("running:", " ".join(command))
        completed = subprocess.run(command, check=False, cwd=project_dir)
        if completed.returncode != 0:
            raise SystemExit(completed.returncode)
    print("release_smoke=passed")


if __name__ == "__main__":
    main()
