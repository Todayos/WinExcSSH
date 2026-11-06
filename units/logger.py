"""File logging with a portable default and an optional path override."""

import logging
import os
from pathlib import Path


logger = logging.getLogger("SSHServiceRunner")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    default_path = Path(__file__).resolve().parent.parent / "logs" / "ssh-service-runner.log"
    configured_path = os.environ.get("SSH_SERVICE_RUNNER_LOG_FILE", os.environ.get("WINEXCSSH_LOG_FILE"))
    log_path = Path(configured_path if configured_path is not None else default_path).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)
