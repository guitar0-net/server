import subprocess
import sys


def run_command(command: list[str], name: str) -> None:
    print(f"{'=' * 33}{name}{'=' * 33}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        print(f"{name} failed")
        sys.exit(1)


def main() -> None:
    run_command([sys.executable, "-m", "ruff", "format", "."], "Ruff Format")
    run_command([sys.executable, "-m", "ruff", "check", ".", "--fix"], "Ruff Check")
    run_command([sys.executable, "-m", "mypy", "."], "Mypy")


if __name__ == "__main__":
    main()
