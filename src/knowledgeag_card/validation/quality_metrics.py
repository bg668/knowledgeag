from __future__ import annotations

from typing import Any

from knowledgeag_card.domain.models import IngestResult


def evaluate_ingest_results(results: list[IngestResult]) -> dict[str, Any]:
    cards = [card for result in results for card in result.cards]
    claims = [claim for result in results for claim in result.claims]
    evidences = [evidence for result in results for evidence in result.evidences]

    report = {
        'card_count': len(cards),
        'claim_count': len(claims),
        'evidence_count': len(evidences),
        'binding_completeness_rate': _binding_completeness_rate(results),
        'coverage_rate': _coverage_rate(results),
        'duplicate_source_count': _duplicate_source_count(results),
        'citation_precision_rate': _citation_precision_rate(results),
        'sources': [_source_report(result) for result in results],
        'comparison': None,
    }
    return report


def build_expected_output(results: list[IngestResult]) -> dict[str, Any]:
    if not results:
        return {
            'expected_source': {},
            'expected_cards': [],
            'expected_claims': [],
            'expected_evidences': [],
        }

    first = results[0]
    evidence_by_id = {
        evidence.evidence_id: evidence
        for result in results
        for evidence in result.evidences
    }
    claim_by_id = {
        claim.claim_id: claim
        for result in results
        for claim in result.claims
    }
    return {
        'expected_source': {
            'title': first.source.title,
            'type': first.source.type.value,
            'source_summary': first.source.source_summary or '',
        },
        'expected_cards': [
            {
                'title': card.title,
                'card_type': card.card_type,
                'applicable_contexts': card.applicable_contexts,
                'core_points': card.core_points,
                'claim_texts': [
                    claim_by_id[claim_id].text
                    for claim_id in card.claim_ids
                    if claim_id in claim_by_id
                ],
                'evidence_quotes': [
                    evidence_by_id[evidence_id].evidence_quote
                    for evidence_id in card.evidence_ids
                    if evidence_id in evidence_by_id
                ],
            }
            for result in results
            for card in result.cards
        ],
        'expected_claims': [
            {
                'text': claim.text,
                'evidence_quotes': [
                    evidence_by_id[evidence_id].evidence_quote
                    for evidence_id in claim.evidence_ids
                    if evidence_id in evidence_by_id
                ],
            }
            for result in results
            for claim in result.claims
        ],
        'expected_evidences': [
            {
                'quote': evidence.evidence_quote,
                'section': _section_from_loc(evidence.loc),
            }
            for result in results
            for evidence in result.evidences
        ],
    }


def compare_expected(
    report: dict[str, Any],
    expected: dict[str, Any],
    *,
    actual_output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    metric_expectations = expected.get('quality_metrics')
    if isinstance(metric_expectations, dict):
        failures.extend(_metric_failures(report, metric_expectations))

    legacy_metric_expectations = {
        metric: expectation
        for metric, expectation in expected.items()
        if metric not in {'quality_metrics', 'expected_source', 'expected_cards', 'expected_claims', 'expected_evidences'}
    }
    failures.extend(_metric_failures(report, legacy_metric_expectations))

    if _has_structured_expected(expected):
        if actual_output is None:
            failures.append('actual_output is required for structured expected comparison')
        else:
            failures.extend(_structured_failures(actual_output, expected))
    return {'passed': not failures, 'failures': failures}


def _metric_failures(report: dict[str, Any], expectations: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for metric, expectation in expectations.items():
        if metric not in report:
            failures.append(f'{metric} is missing from report')
            continue
        actual = report[metric]
        if _is_threshold(expectation):
            failures.extend(_threshold_failures(metric, actual, expectation))
            continue
        if actual != expectation:
            failures.append(f'{metric} expected == {expectation}, got {actual}')
    return failures


def _binding_completeness_rate(results: list[IngestResult]) -> float:
    complete = 0
    total = 0
    for result in results:
        claims_by_id = {claim.claim_id: claim for claim in result.claims}
        evidence_ids = {evidence.evidence_id for evidence in result.evidences}
        for card in result.cards:
            card_evidence_ids = set(card.evidence_ids)
            for claim_id in card.claim_ids:
                total += 1
                claim = claims_by_id.get(claim_id)
                if claim is None or not claim.evidence_ids:
                    continue
                claim_evidence_ids = set(claim.evidence_ids)
                if claim_evidence_ids <= evidence_ids and claim_evidence_ids <= card_evidence_ids:
                    complete += 1
    return _rate(complete, total)


def _coverage_rate(results: list[IngestResult]) -> float:
    covered = 0
    total = 0
    for result in results:
        if result.source_coverage is None:
            continue
        covered += len(result.source_coverage.covered_sections)
        total += len(result.source_coverage.source_sections)
    return _rate(covered, total)


def _duplicate_source_count(results: list[IngestResult]) -> int:
    seen: set[tuple[str, str]] = set()
    duplicates = 0
    for result in results:
        key = (result.source.uri, result.source.version_id)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
    return duplicates


def _citation_precision_rate(results: list[IngestResult]) -> float:
    precise = 0
    total = 0
    for result in results:
        for evidence in result.evidences:
            total += 1
            if evidence.evidence_quote and evidence.loc and evidence.evidence_quote in evidence.content:
                precise += 1
    return _rate(precise, total)


def _source_report(result: IngestResult) -> dict[str, Any]:
    return {
        'source_id': result.source.source_id,
        'title': result.source.title,
        'uri': result.source.uri,
        'version_id': result.source.version_id,
        'card_count': len(result.cards),
        'claim_count': len(result.claims),
        'evidence_count': len(result.evidences),
        'coverage_rate': _coverage_rate([result]),
    }


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _is_threshold(expectation: Any) -> bool:
    return isinstance(expectation, dict) and any(key in expectation for key in ('min', 'max', 'eq'))


def _threshold_failures(metric: str, actual: Any, expectation: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if 'min' in expectation and actual < expectation['min']:
        failures.append(f'{metric} expected >= {expectation["min"]}, got {actual}')
    if 'max' in expectation and actual > expectation['max']:
        failures.append(f'{metric} expected <= {expectation["max"]}, got {actual}')
    if 'eq' in expectation and actual != expectation['eq']:
        failures.append(f'{metric} expected == {expectation["eq"]}, got {actual}')
    return failures


def _has_structured_expected(expected: dict[str, Any]) -> bool:
    return any(key in expected for key in ('expected_source', 'expected_cards', 'expected_claims', 'expected_evidences'))


def _structured_failures(actual_output: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    failures.extend(_source_failures(actual_output.get('expected_source', {}), expected.get('expected_source')))
    failures.extend(_card_failures(actual_output.get('expected_cards', []), expected.get('expected_cards', [])))
    failures.extend(_claim_failures(actual_output.get('expected_claims', []), expected.get('expected_claims', [])))
    failures.extend(
        _evidence_failures(actual_output.get('expected_evidences', []), expected.get('expected_evidences', []))
    )
    return failures


def _source_failures(actual_source: dict[str, Any], expected_source: Any) -> list[str]:
    if not isinstance(expected_source, dict):
        return []

    failures: list[str] = []
    for key, expected_value in expected_source.items():
        if key == 'source_summary_contains':
            summary = actual_source.get('source_summary', '')
            for text in expected_value:
                if text not in summary:
                    failures.append(f'expected_source source_summary missing text: {text}')
            continue
        actual_value = actual_source.get(key)
        if actual_value != expected_value:
            failures.append(f'expected_source {key} expected == {expected_value}, got {actual_value}')
    return failures


def _card_failures(actual_cards: list[dict[str, Any]], expected_cards: Any) -> list[str]:
    if not isinstance(expected_cards, list):
        return []

    failures: list[str] = []
    all_core_points = {
        core_point
        for card in actual_cards
        for core_point in card.get('core_points', [])
    }
    for index, expected_card in enumerate(expected_cards):
        if not isinstance(expected_card, dict):
            continue
        title = expected_card.get('title')
        matching_card = _find_by_value(actual_cards, 'title', title)
        if title and matching_card is None:
            failures.append(f'expected_cards[{index}] title not found: {title}')
        expected_core_points = expected_card.get('core_points', [])
        actual_core_points = set(matching_card.get('core_points', [])) if matching_card else all_core_points
        for core_point in expected_core_points:
            if core_point not in actual_core_points:
                failures.append(f'expected_cards[{index}] core_point not found: {core_point}')
    return failures


def _claim_failures(actual_claims: list[dict[str, Any]], expected_claims: Any) -> list[str]:
    if not isinstance(expected_claims, list):
        return []

    failures: list[str] = []
    for index, expected_claim in enumerate(expected_claims):
        if not isinstance(expected_claim, dict):
            continue
        text = expected_claim.get('text')
        matching_claim = _find_by_value(actual_claims, 'text', text)
        if text and matching_claim is None:
            failures.append(f'expected_claims[{index}] text not found: {text}')
            continue
        actual_quotes = set(matching_claim.get('evidence_quotes', [])) if matching_claim else set()
        for quote in expected_claim.get('evidence_quotes', []):
            if quote not in actual_quotes:
                failures.append(f'expected_claims[{index}] evidence_quote not found: {quote}')
    return failures


def _evidence_failures(actual_evidences: list[dict[str, Any]], expected_evidences: Any) -> list[str]:
    if not isinstance(expected_evidences, list):
        return []

    failures: list[str] = []
    actual_quotes = {evidence.get('quote') for evidence in actual_evidences}
    actual_sections = {evidence.get('section') for evidence in actual_evidences}
    for index, expected_evidence in enumerate(expected_evidences):
        if not isinstance(expected_evidence, dict):
            continue
        quote = expected_evidence.get('quote')
        section = expected_evidence.get('section')
        if quote and quote not in actual_quotes:
            failures.append(f'expected_evidences[{index}] quote not found: {quote}')
        if section and section not in actual_sections:
            failures.append(f'expected_evidences[{index}] section not found: {section}')
    return failures


def _find_by_value(items: list[dict[str, Any]], key: str, value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    for item in items:
        if item.get(key) == value:
            return item
    return None


def _section_from_loc(loc: str) -> str:
    for part in loc.split(';'):
        part = part.strip()
        if part.startswith('section='):
            return part.removeprefix('section=').strip()
    return ''
