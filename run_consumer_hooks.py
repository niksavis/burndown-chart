import subprocess

from validate import PYTHON, ROOT


def main() -> int:
    if not PYTHON.is_file():
        raise SystemExit(
            "Create .venv and install requirements-dev.txt before committing"
        )
    return subprocess.run(
        [
            str(PYTHON),
            "-m",
            "pre_commit",
            "run",
            "--config",
            ".pre-commit-consumer.yaml",
        ],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
