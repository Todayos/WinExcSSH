"""Check log directory creation and imports in a clean subprocess."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class LoggingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "renamed project"
        (self.project / "units").mkdir(parents=True)
        source = Path(__file__).resolve().parent.parent / "units" / "logger.py"
        shutil.copyfile(source, self.project / "units" / "logger.py")
        self.environment = {key: value for key, value in os.environ.items()
                            if not key.startswith(("SSH_SERVICE_RUNNER_", "WINEXCSSH_"))}

    def run_logger(self):
        script = (
            "import importlib, sys\n"
            f"sys.path.insert(0, {str(self.project)!r})\n"
            "from units import logger as module\n"
            "importlib.reload(module)\n"
            "module.logger.info('Log entry: caf\\u00e9')\n"
            "assert len(module.logger.handlers) == 1\n"
            "for handler in module.logger.handlers: handler.flush()\n"
        )
        result = subprocess.run([sys.executable, "-c", script], cwd=self.root,
                                env=self.environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_log_is_relative_to_project_and_not_duplicated(self):
        self.run_logger()
        content = (self.project / "logs" / "ssh-service-runner.log").read_text(encoding="utf-8")
        self.assertEqual(content.count("Log entry: caf\u00e9"), 1)

    def test_override_creates_nested_directories(self):
        target = self.root / "nested" / "logs" / "custom.log"
        self.environment["SSH_SERVICE_RUNNER_LOG_FILE"] = str(target)
        self.run_logger()
        self.assertIn("Log entry: caf\u00e9", target.read_text(encoding="utf-8"))

    def test_current_log_variable_takes_precedence_over_legacy_variable(self):
        target = self.root / "current.log"
        legacy = self.root / "legacy.log"
        self.environment["SSH_SERVICE_RUNNER_LOG_FILE"] = str(target)
        self.environment["WINEXCSSH_LOG_FILE"] = str(legacy)
        self.run_logger()
        self.assertTrue(target.is_file())
        self.assertFalse(legacy.exists())

    def test_legacy_log_variable_remains_supported(self):
        target = self.root / "legacy.log"
        self.environment["WINEXCSSH_LOG_FILE"] = str(target)
        self.run_logger()
        self.assertTrue(target.is_file())


if __name__ == "__main__":
    unittest.main()
