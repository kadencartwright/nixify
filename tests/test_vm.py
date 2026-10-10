import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vm", ROOT / ".agents/skills/nixify-vm/scripts/vm.py")
vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vm)


class VMHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.flake = self.root / "config with spaces"
        self.flake.mkdir()
        (self.flake / "flake.nix").write_text("{}")
        self.work = self.root / "private-vm"
        self.args = ["--flake", str(self.flake), "--host", "demo-arm", "--work-dir", str(self.work)]
        self.nix = patch.object(vm.shutil, "which", return_value="/bin/nix")
        self.nix.start()
        self.addCleanup(self.nix.stop)

    def test_check_only_evaluates_selected_guest_and_preserves_lock(self):
        with patch.object(vm, "invoke") as invoke:
            self.assertEqual(vm.main(self.args + ["check"]), 0)
        command = invoke.call_args.args[0]
        self.assertIn("eval", command)
        self.assertIn(f"{self.flake}#nixosConfigurations.demo-arm.config.system.build.vm.drvPath", command)
        self.assertIn("--no-update-lock-file", command)
        self.assertFalse(self.work.exists())

    def test_untracked_source_requires_explicit_option(self):
        with patch.object(vm, "invoke") as invoke:
            vm.main(self.args + ["--include-untracked", "check"])
        self.assertIn(f"path:{self.flake}#nixosConfigurations.demo-arm.config.system.build.vm.drvPath",
                      invoke.call_args.args[0])

    def test_dry_build_does_not_launch_or_create_disk(self):
        with patch.object(vm, "invoke") as invoke:
            vm.main(self.args + ["dry-build"])
        self.assertIn("--dry-run", invoke.call_args.args[0])
        self.assertEqual(invoke.call_count, 1)
        self.assertFalse(self.work.exists())

    def test_run_uses_separate_disk_and_preserves_existing_contents(self):
        bin_dir = self.work / "result-vm/bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "run-demo-vm").write_text("#!/bin/sh\n")
        disk = self.work / "guest.qcow2"
        disk.write_bytes(b"existing guest data")
        with patch.object(vm.platform, "system", return_value="Linux"), patch.object(vm, "invoke") as invoke, \
             patch.dict(os.environ, {"NIX_DISK_IMAGE": "/dev/dangerous"}):
            vm.main(self.args + ["run"])
        self.assertEqual(invoke.call_count, 2)
        launch = invoke.call_args
        self.assertEqual(launch.kwargs["env"]["NIX_DISK_IMAGE"], str(disk))
        self.assertEqual(launch.kwargs["cwd"], self.work)
        self.assertEqual(disk.read_bytes(), b"existing guest data")

    def test_darwin_run_refuses_before_build_or_disk_creation(self):
        with patch.object(vm.platform, "system", return_value="Darwin"), patch.object(vm, "invoke") as invoke:
            with self.assertRaises(SystemExit):
                vm.main(self.args + ["run"])
        invoke.assert_not_called()
        self.assertFalse(self.work.exists())

    def test_work_directory_inside_flake_is_rejected(self):
        with patch.object(vm, "invoke") as invoke:
            with self.assertRaises(SystemExit):
                vm.main(["build", "--flake", str(self.flake), "--work-dir", str(self.flake / "vm")])
        invoke.assert_not_called()

    def test_invalid_output_name_is_rejected_without_invoking_nix(self):
        with patch.object(vm, "invoke") as invoke:
            with self.assertRaises(SystemExit):
                vm.main(["check", "--flake", str(self.flake), "--host", "demo; touch bad"])
        invoke.assert_not_called()

    def test_symlinked_disk_is_rejected(self):
        bin_dir = self.work / "result-vm/bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "run-demo-vm").write_text("#!/bin/sh\n")
        target = self.root / "important"
        target.write_text("retain")
        (self.work / "guest.qcow2").symlink_to(target)
        with patch.object(vm.platform, "system", return_value="Linux"), patch.object(vm, "invoke") as invoke:
            with self.assertRaises(RuntimeError):
                vm.main(self.args + ["run"])
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(target.read_text(), "retain")


if __name__ == "__main__":
    unittest.main()
