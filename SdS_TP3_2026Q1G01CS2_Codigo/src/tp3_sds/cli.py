from __future__ import annotations

import argparse
from pathlib import Path

from tp3_sds.system1.config import load_config, validate_config
from tp3_sds.system1.simulation import run_simulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tp3")
    subparsers = parser.add_subparsers(dest="command", required=True)
    system1_parser = subparsers.add_parser("system1")
    system1_subparsers = system1_parser.add_subparsers(dest="system1_command", required=True)

    validate_parser = system1_subparsers.add_parser("validate-config")
    validate_parser.add_argument("--config", required=True, type=Path)

    run_parser = system1_subparsers.add_parser("run")
    run_parser.add_argument("--config", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config.resolve())
    validation = validate_config(config)

    if args.system1_command == "validate-config":
        if validation.errors:
            print("Config validation failed:")
            for error in validation.errors:
                print(f"- {error}")
            return 1
        print("Config validation passed.")
        for warning in validation.warnings:
            print(f"- warning: {warning}")
        return 0

    if validation.errors:
        print("Config validation failed:")
        for error in validation.errors:
            print(f"- {error}")
        return 1
    result = run_simulation(config, config_path=args.config.resolve())
    print(f"Wrote animator output to {result.output_path}")
    print(f"Processed events: {result.processed_events}")
    print(f"Snapshots written: {result.snapshots_written}")
    print(f"Scanning count: {result.scanning_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
