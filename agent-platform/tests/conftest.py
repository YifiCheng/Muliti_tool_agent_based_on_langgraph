import os
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
TEST_CONFIG = APP_ROOT / "config" / "config.test.yaml"

os.environ["AGENT_CONFIG_PATH"] = str(TEST_CONFIG)