import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("discover", ROOT / ".agents/skills/nixify-discover/scripts/discover.py")
discover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(discover)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def scan(self, **kwargs):
        inventory = discover.Inventory()
        discover.scan_root(inventory, self.root, kwargs.get("max_depth", 5),
                           [kwargs.get("max_files", 2000)], kwargs.get("max_bytes", 524288))
        return inventory.finish()

    def test_runtime_versions_and_managers_preserve_evidence(self):
        self.write("web/package.json", json.dumps({"engines": {"node": ">=22"},
                                                   "packageManager": "pnpm@10.0.0",
                                                   "dependencies": {"react": "19"}}))
        self.write("api/pyproject.toml", '[project]\nrequires-python = ">=3.12"\n[tool.uv]\n')
        data = self.scan()
        candidates = {x["nix_attribute"]: x for x in data["candidates"]}
        self.assertEqual(set(candidates), {"nodejs", "pnpm", "python3", "uv"})
        self.assertEqual(candidates["nodejs"]["evidence"][0]["declared_version"], ">=22")
        self.assertTrue(all(x["scope"] == "devShell" and not x["verified"] for x in candidates.values()))

    def test_does_not_execute_project_code_or_read_secrets(self):
        self.write("package.json", '{"scripts":{"postinstall":"touch SENTINEL"}}')
        self.write(".env", "SECRET=do-not-report-me")
        self.write("flake.nix", 'builtins.abort "should never evaluate"')
        with patch.object(subprocess, "run", side_effect=AssertionError("Project execution")):
            data = self.scan()
        self.assertFalse((self.root / "SENTINEL").exists())
        self.assertNotIn("do-not-report-me", json.dumps(data))
        self.assertEqual(len(data["projects"]), 2)

    def test_symlinked_files_directories_and_dependencies_are_skipped(self):
        outside = self.write("private/hidden.json", '{"engines":{"node":"99"}}')
        (self.root / "package.json").symlink_to(outside)
        (self.root / "linked").symlink_to(outside.parent, target_is_directory=True)
        self.write("node_modules/a/pyproject.toml", "[project]\n")
        data = self.scan()
        self.assertFalse(data["candidates"])
        self.assertTrue(any("symlink" in x for x in data["warnings"]))

    def test_brew_casks_remain_unmapped_and_taps_are_ignored(self):
        self.write("Brewfile", 'tap "homebrew/core"\nbrew "ripgrep"\ncask "visual-studio-code"\nbrew "unknown-internal-tool"\n')
        data = self.scan()
        self.assertEqual([x["nix_attribute"] for x in data["candidates"]], ["ripgrep"])
        self.assertEqual({x["name"] for x in data["unmapped_packages"]},
                         {"visual-studio-code", "unknown-internal-tool"})
        self.assertEqual(len(data["installed_packages"]), 3)

    def test_depth_file_and_size_limits_are_reported(self):
        self.write("package.json", " " * 101)
        self.write("nested/pyproject.toml", "[project]\n")
        data = self.scan(max_depth=0, max_bytes=100)
        self.assertFalse(data["candidates"])
        self.assertTrue(any("Depth limit" in x for x in data["warnings"]))
        self.assertTrue(any("Oversized" in x for x in data["warnings"]))
        data = self.scan(max_files=1)
        self.assertTrue(any("Manifest limit" in x for x in data["warnings"]))

    def test_malformed_manifest_does_not_hide_other_projects_or_echo_content(self):
        self.write("package.json", '{"secret": "not-to-echo", BROKEN}')
        self.write("go.mod", "module example.org/project\ngo 1.24\n")
        data = self.scan()
        self.assertEqual([x["nix_attribute"] for x in data["candidates"]], ["go"])
        self.assertTrue(data["warnings"])
        self.assertNotIn("not-to-echo", json.dumps(data))

    def test_existing_nix_files_are_evidence_only(self):
        self.write("shell.nix", 'builtins.abort "no execution"')
        data = self.scan()
        self.assertEqual(len(data["projects"]), 1)
        self.assertFalse(data["candidates"])

    def test_host_inventory_requires_opt_in(self):
        with patch.object(discover.shutil, "which", return_value=None), \
             patch.object(discover, "host_packages") as query, \
             contextlib.redirect_stdout(io.StringIO()):
            discover.main(["--repo", str(self.root)])
            query.assert_not_called()
            discover.main(["--repo", str(self.root), "--host-packages"])
            query.assert_called_once()

    def test_host_package_queries_are_read_only_and_time_bounded(self):
        def which(name):
            return f"/bin/{name}" if name == "brew" else None
        with patch.object(discover.shutil, "which", side_effect=which), \
             patch.object(discover.platform, "system", return_value="Darwin"), \
             patch.object(discover.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "git\n")) as run:
            inventory = discover.Inventory()
            discover.host_packages(inventory)
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][:2], ["brew", "list"])
            self.assertEqual(call.kwargs["timeout"], 20)
            self.assertEqual(call.kwargs["env"]["HOMEBREW_NO_AUTO_UPDATE"], "1")

    def test_missing_root_and_symlink_root_fail(self):
        with self.assertRaises(ValueError):
            discover.scan_root(discover.Inventory(), self.root / "missing", 5, [10], 100)
        linked = self.root / "alias"
        linked.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            discover.scan_root(discover.Inventory(), linked, 5, [10], 100)

    def test_cli_json_and_global_manifest_limit(self):
        self.write("package.json", "{}")
        second = self.root / "second"
        self.write("second/go.mod", "go 1.24\n")
        output = io.StringIO()
        with patch.object(discover.shutil, "which", return_value=None), contextlib.redirect_stdout(output):
            discover.main(["--repo", str(self.root), "--repo", str(second), "--max-files", "1"])
        data = json.loads(output.getvalue())
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(len(data["projects"]), 1)
        self.assertTrue(data["warnings"])


if __name__ == "__main__":
    unittest.main()
