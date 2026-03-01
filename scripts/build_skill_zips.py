#!/usr/bin/env python3
"""Build distributable skill ZIP archives from skills/* folders.

By default, archives are written to ./dist/skills-zips to avoid binary changes in PRs.
Use --output skills-zips only when preparing release artifacts intentionally.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import zipfile

SKILLS = [
    "machine-vibration-monitoring",
    "operator-diagnostic-report",
    "vibration-fault-diagnosis",
]


def build_zip(skill_dir: Path, output_zip: Path) -> int:
    files = sorted([p for p in skill_dir.rglob("*") if p.is_file()])
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            zf.write(file_path, file_path.relative_to(skill_dir).as_posix())
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build skill zip archives")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/skills-zips"),
        help="Output directory for generated ZIP files (default: dist/skills-zips)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    skills_root = repo_root / "skills"
    out_root = (repo_root / args.output).resolve() if not args.output.is_absolute() else args.output

    for skill_name in SKILLS:
        skill_dir = skills_root / skill_name
        if not skill_dir.exists():
            raise FileNotFoundError(f"Missing skill directory: {skill_dir}")
        out_zip = out_root / f"{skill_name}.zip"
        count = build_zip(skill_dir, out_zip)
        print(f"built {out_zip} ({count} files)")

    print("Done. Note: keep ZIP binaries out of normal PRs unless explicitly required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
