from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from knowledgeag_card.runtime.agent_app import AgentApp
from knowledgeag_card.validation.quality_metrics import (
    build_expected_output,
    compare_expected,
    evaluate_ingest_results,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--expected', help='expected quality metrics JSON')
    args = parser.parse_args(argv)

    results = AgentApp.create().ingest(args.path)
    report = evaluate_ingest_results(results)
    if args.expected:
        expected = json.loads(Path(args.expected).read_text(encoding='utf-8'))
        report['comparison'] = compare_expected(
            report,
            expected,
            actual_output=build_expected_output(results),
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    comparison = report.get('comparison')
    if comparison is not None and not comparison['passed']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
