"""Vendor deduplication step - merges duplicate vendor entries."""

import logging
from difflib import SequenceMatcher

from app.services.pipeline.steps.extract import ExtractedVendor

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    """Normalize vendor name for comparison."""
    # Remove common suffixes and lowercase
    name = name.lower().strip()
    for suffix in [
        " inc", " inc.", " incorporated",
        " llc", " ltd", " ltd.", " limited",
        " corp", " corp.", " corporation",
        " co", " co.", " company",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()


def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    url = url.lower().strip()
    # Remove protocol
    for prefix in ["https://", "http://", "www."]:
        if url.startswith(prefix):
            url = url[len(prefix):]
    # Remove trailing slash
    return url.rstrip("/")


def similarity_score(a: str, b: str) -> float:
    """Calculate string similarity score (0-1)."""
    return SequenceMatcher(None, a, b).ratio()


def are_duplicates(v1: ExtractedVendor, v2: ExtractedVendor) -> bool:
    """Check if two vendors are likely duplicates."""
    # Exact name match
    norm1 = normalize_name(v1.name)
    norm2 = normalize_name(v2.name)
    if norm1 == norm2:
        return True

    # High name similarity
    if similarity_score(norm1, norm2) > 0.85:
        return True

    # Same website domain
    if v1.data.get("website") and v2.data.get("website"):
        url1 = normalize_url(v1.data["website"])
        url2 = normalize_url(v2.data["website"])
        # Extract domain
        domain1 = url1.split("/")[0]
        domain2 = url2.split("/")[0]
        if domain1 == domain2:
            return True

    return False


def merge_vendors(primary: ExtractedVendor, secondary: ExtractedVendor) -> ExtractedVendor:
    """Merge two vendor records, preferring non-null values from primary."""
    merged_data = dict(primary.data)

    # Fill in missing fields from secondary
    for key, value in secondary.data.items():
        if not merged_data.get(key) and value:
            merged_data[key] = value

    # Combine evidence
    merged_evidence = list(primary.evidence)
    for ev in secondary.evidence:
        if ev not in merged_evidence:
            merged_evidence.append(ev)

    return ExtractedVendor(
        name=primary.name,
        source_url=primary.source_url,
        source_title=primary.source_title,
        data=merged_data,
        evidence=merged_evidence,
    )


def deduplicate_vendors(vendors: list[ExtractedVendor]) -> list[ExtractedVendor]:
    """
    Deduplicate vendor list by merging similar entries.

    Args:
        vendors: List of extracted vendors

    Returns:
        Deduplicated list with merged data
    """
    if not vendors:
        return []

    deduped: list[ExtractedVendor] = []

    for vendor in vendors:
        merged = False
        for i, existing in enumerate(deduped):
            if are_duplicates(vendor, existing):
                deduped[i] = merge_vendors(existing, vendor)
                merged = True
                break
        if not merged:
            deduped.append(vendor)

    logger.info(f"Deduplicated {len(vendors)} vendors to {len(deduped)} unique entries")
    return deduped
