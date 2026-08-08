import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


REQUIRED_FILES = [
    "package.json",
    "vite.config.ts",
    "src/main.tsx",
    "src/App.tsx",
    "src/api.ts",
    "src/components/AgentConsole.tsx",
    "src/components/EvidencePanel.tsx",
    "src/components/TracePanel.tsx",
    "src/components/StatusPanel.tsx",
    "src/components/ReportPanel.tsx",
]


def main() -> None:
    missing = [
        item
        for item in REQUIRED_FILES
        if not (FRONTEND / item).exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing frontend files: {missing}")

    package_json = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    deps = {
        **package_json.get("dependencies", {}),
        **package_json.get("devDependencies", {}),
    }
    for package in ["@vitejs/plugin-react", "typescript", "vite", "react", "react-dom"]:
        if package not in deps:
            raise RuntimeError(f"Missing frontend dependency: {package}")

    print("smoke_frontend_react=ready")


if __name__ == "__main__":
    main()