"""Verify portable entry points using an intentionally incomplete template."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class StartupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = Path(__file__).resolve().parent.parent
        self.environment = {key: value for key, value in os.environ.items()
                            if not key.startswith(("SSH_SERVICE_RUNNER_", "WINEXCSSH_"))}

    def copy_project(self, directory_name):
        destination = self.root / directory_name
        destination.mkdir()
        shutil.copyfile(self.source / "start.py", destination / "start.py")
        for directory in ("config", "core", "units"):
            shutil.copytree(self.source / directory, destination / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "config.local*"))
        # Force a blank host, independent of any settings in the source checkout.
        (destination / "config" / "config.yml").write_text("HostInfo: {IP: ''}\n", encoding="utf-8")
        return destination

    def assert_template_error(self, arguments):
        result = subprocess.run([sys.executable, *arguments], cwd=self.root,
                                env=self.environment, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HostInfo.IP must be a non-empty string", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_script_runs_from_renamed_directory_and_another_working_directory(self):
        project = self.copy_project("renamed project with spaces")
        self.assert_template_error([str(project / "start.py")])
        self.assertTrue((project / "logs" / "ssh-service-runner.log").is_file())

    def test_package_entry_point_keeps_relative_imports_working(self):
        self.copy_project("portable_project")
        self.assert_template_error(["-m", "portable_project.start"])


if __name__ == "__main__":
    unittest.main()
