#!/usr/bin/env python3
"""将真实 Hub 的公开 Department 投影与唯一 YAML 声明逐项比对。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


EXPECTED_IDS = ["strategist", "researcher", "builder", "growth"]
PUBLIC_KEYS = {"id", "name", "description"}
FORBIDDEN_KEYS = {
    "model",
    "provider",
    "skills",
    "mcp_config",
    "system_prompt",
    "heartbeat_secs",
    "agent_spec",
    "charter",
    "permissions",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("departments_dir", type=Path)
    parser.add_argument("options", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    options = json.loads(args.options.read_text(encoding="utf-8"))
    assert [row["id"] for row in options] == EXPECTED_IDS
    assert all(set(row) == PUBLIC_KEYS for row in options)

    expected = []
    for department_id in EXPECTED_IDS:
        source = args.departments_dir / f"{department_id}.yaml"
        row = yaml.safe_load(source.read_text(encoding="utf-8"))
        expected.append(
            {
                "id": department_id,
                "name": row["public_name"],
                "description": row["public_description"],
            }
        )
    assert options == expected

    serialized = json.dumps(options, ensure_ascii=False)
    leaked = sorted(key for key in FORBIDDEN_KEYS if f'"{key}"' in serialized)
    assert not leaked
    assert not (args.departments_dir / "catalog.yaml").exists()

    result = {
        "passed": True,
        "source_of_truth": "agents/departments/<fixed-id>.yaml",
        "ids_in_order": EXPECTED_IDS,
        "option_count": len(options),
        "exact_keys": sorted(PUBLIC_KEYS),
        "yaml_values_match": True,
        "forbidden_keys_found": leaked,
        "catalog_absent": True,
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
