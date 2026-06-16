from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Sequence

if TYPE_CHECKING:
    from renderpapers.models import Paper


class QueryError(ValueError):
    """Raised when structured query arguments are not searchable."""


def _flatten_terms(groups: Sequence[Sequence[str]] | None) -> tuple[str, ...]:
    if not groups:
        return ()
    terms: list[str] = []
    for group in groups:
        for term in group:
            cleaned = term.strip()
            if cleaned:
                terms.append(cleaned)
    return tuple(terms)


@dataclass(frozen=True)
class StructuredQuery:
    base: str = ""
    all_terms: tuple[str, ...] = ()
    any_terms: tuple[str, ...] = ()
    not_terms: tuple[str, ...] = ()

    @classmethod
    def from_cli(
        cls,
        base: str | None,
        all_terms: Sequence[Sequence[str]] | None = None,
        any_terms: Sequence[Sequence[str]] | None = None,
        not_terms: Sequence[Sequence[str]] | None = None,
    ) -> "StructuredQuery":
        return cls(
            base=(base or "").strip(),
            all_terms=_flatten_terms(all_terms),
            any_terms=_flatten_terms(any_terms),
            not_terms=_flatten_terms(not_terms),
        )

    @property
    def has_structured_terms(self) -> bool:
        return bool(self.all_terms or self.any_terms or self.not_terms)

    @property
    def has_positive_terms(self) -> bool:
        return bool(self.base or self.all_terms or self.any_terms)

    def require_searchable(self) -> None:
        if not self.has_positive_terms:
            raise QueryError("Search needs a query, --all term, or --any term.")

    def display(self) -> str:
        parts: list[str] = []
        if self.base:
            parts.append(self.base)
        if self.all_terms:
            parts.append("AND " + ", ".join(self.all_terms))
        if self.any_terms:
            parts.append("OR " + ", ".join(self.any_terms))
        if self.not_terms:
            parts.append("NOT " + ", ".join(self.not_terms))
        return " | ".join(parts)


def _quote_arxiv_term(term: str) -> str:
    escaped = term.replace('"', r"\"")
    if any(char.isspace() for char in escaped):
        return f'all:"{escaped}"'
    return f"all:{escaped}"


def compile_arxiv_query(query: StructuredQuery) -> str:
    query.require_searchable()
    parts: list[str] = []
    if query.base:
        parts.append(query.base)
    parts.extend(_quote_arxiv_term(term) for term in query.all_terms)
    if query.any_terms:
        parts.append("(" + " OR ".join(_quote_arxiv_term(term) for term in query.any_terms) + ")")

    compiled = " AND ".join(f"({part})" if " AND " in part or " OR " in part else part for part in parts)
    for term in query.not_terms:
        compiled = f"({compiled}) ANDNOT {_quote_arxiv_term(term)}"
    return compiled


def compile_semantic_query(query: StructuredQuery) -> str:
    query.require_searchable()
    terms: list[str] = []
    if query.base:
        terms.append(query.base)
    terms.extend(query.all_terms)
    terms.extend(query.any_terms)
    return " ".join(terms)


def _paper_search_text(paper: Paper) -> str:
    fields: Iterable[str] = (
        paper.title,
        paper.abstract,
        paper.venue or "",
        paper.journal_ref or "",
        paper.tldr or "",
        " ".join(paper.authors),
        " ".join(paper.categories),
    )
    return " ".join(field for field in fields if field).lower()


def matches_structured_query(paper: Paper, query: StructuredQuery) -> bool:
    if not query.has_structured_terms:
        return True
    text = _paper_search_text(paper)
    all_terms_match = all(term.lower() in text for term in query.all_terms)
    any_terms_match = not query.any_terms or any(term.lower() in text for term in query.any_terms)
    not_terms_match = not any(term.lower() in text for term in query.not_terms)
    return all_terms_match and any_terms_match and not_terms_match


def filter_structured_results(papers: Sequence[Paper], query: StructuredQuery) -> list[Paper]:
    if not query.has_structured_terms:
        return list(papers)
    return [paper for paper in papers if matches_structured_query(paper, query)]
