import difflib

from foi_system.models import ComplianceResult, RetrievedChunk

_QUOTE_MATCH_THRESHOLD = 0.85


def _normalize(s: str) -> str:
    # collapse whitespace + lowercase so formatting/case differences don't fail a true quote
    return " ".join(s.split()).lower()


def _quote_coverage(quote: str, chunk_text: str) -> float:
    q, ch = _normalize(quote), _normalize(chunk_text)
    if not q:
        return 0.0
    if q in ch:  # exact verbatim substring
        return 1.0
    sm = difflib.SequenceMatcher(None, q, ch, autojunk=False)
    matched = sum(block.size for block in sm.get_matching_blocks())
    return matched / len(q)  # fraction of the quote found in the chunk


def verify_citations(
    result: ComplianceResult, chunks: list[RetrievedChunk]
) -> tuple[bool, list[str]]:
    problems: list[str] = []
    sources = {(c.source, c.chunk_index): c.text for c in chunks}
    for finding in result.exemptions:
        for cit in finding.citations:
            key = (cit.source, cit.chunk_index)
            if key not in sources:  # L1
                problems.append(
                    f"{cit.section}: cited chunk {cit.source}#{cit.chunk_index} not retrieved"
                )
            else:  # L2
                cov = _quote_coverage(cit.quote, sources[key])
                if cov < _QUOTE_MATCH_THRESHOLD:
                    problems.append(f"{cit.section}: quote not found verbatim (coverage {cov:.2f})")
    return (not problems, problems)
