#!/usr/bin/env python3
"""Validate packaged skills and run meaningful helper tests."""

from pathlib import Path
import re
import shutil
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    failures = []
    skills = sorted((ROOT / ".agents/skills").glob("*/SKILL.md"))
    if len(skills) != 4:
        failures.append(f"Expected four skill entrypoints, found {len(skills)}")
    for skill in skills:
        text = skill.read_text()
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not match:
            failures.append(f"{skill}: missing YAML frontmatter")
            continue
        metadata = yaml.safe_load(match[1])
        if not isinstance(metadata, dict):
            failures.append(f"{skill}: frontmatter must be a mapping")
            continue
        name = metadata.get("name", "")
        if name != skill.parent.name or not re.fullmatch(r"[a-z0-9-]{1,63}", name):
            failures.append(f"{skill}: invalid or mismatched name")
        if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
            failures.append(f"{skill}: missing description")
        if re.search(r"\[TODO\]|\[INSERT[^\]]*\]", text, re.I):
            failures.append(f"{skill}: unfinished scaffold")
        ui = yaml.safe_load((skill.parent / "agents/openai.yaml").read_text())
        interface = ui.get("interface", {})
        if f"${name}" not in interface.get("default_prompt", ""):
            failures.append(f"{skill}: default prompt must name the skill")
        length = len(interface.get("short_description", ""))
        if not 25 <= length <= 64:
            failures.append(f"{skill}: short description must be 25–64 characters")
        for document in [skill, *skill.parent.glob("references/*.md")]:
            for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
                if re.match(r"[a-z]+://|#", target):
                    continue
                if not (document.parent / target.split("#")[0]).exists():
                    failures.append(f"{document}: broken local reference {target}")
    for document in [*ROOT.glob("*.md"), *ROOT.glob("examples/*.md")]:
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if re.match(r"[a-z]+://|#", target):
                continue
            if not (document.parent / target.split("#")[0]).exists():
                failures.append(f"{document}: broken local reference {target}")
    for script in ROOT.rglob("*.sh"):
        subprocess.run(["bash", "-n", str(script)], check=True)
    if shutil.which("nix-instantiate"):
        for expression in ROOT.rglob("*.nix"):
            subprocess.run(["nix-instantiate", "--parse", str(expression)], check=True,
                           stdout=subprocess.DEVNULL)
    else:
        print("Nix syntax check skipped: nix-instantiate unavailable (CI evaluates Nix).")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Validated {len(skills)} skills and their references.")
    return subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                          cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())
