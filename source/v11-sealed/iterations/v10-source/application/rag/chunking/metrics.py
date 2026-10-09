"""Structural measurements, not retrieval quality estimates."""
from dataclasses import asdict
from .models import Containment


def compare(service, evidence_ids, policies):
    rows = []
    for policy in policies:
        chunks, support_ids, claim_ids, full_supports, full_claims, partial = [], set(), set(), set(), set(), set()
        total_chars = 0
        deterministic = True
        for evidence_id in evidence_ids:
            batch = service.generate(evidence_id, policy)
            deterministic &= batch == service.generate(evidence_id, policy)
            chunks.extend(batch)
            if batch:
                total_chars += batch[-1].end
            for chunk in batch:
                for link in chunk.claim_links:
                    support_ids.add(link.support.support_id)
                    claim_ids.add(link.support.claim_id)
                    if link.containment == Containment.FULLY_CONTAINED:
                        full_supports.add(link.support.support_id)
                        full_claims.add(link.support.claim_id)
                    else:
                        partial.add(link.support.claim_id)
        represented = sum(len(c.text) for c in chunks)
        citation_successes = sum(service.cite(c.chunk_id, c.revision_id).chunk.text == c.text for c in chunks)
        rows.append({'policy': asdict(policy), 'policy_id': policy.policy_id,
                     'chunk_count': len(chunks),
                     'average_size': sum(c.measured_size for c in chunks) / len(chunks) if chunks else 0,
                     'source_characters': total_chars, 'represented_characters': represented,
                     'overlap_duplication_ratio': (represented - total_chars) / total_chars if total_chars else 0,
                     'unique_claims': len(claim_ids), 'support_occurrences': len(support_ids),
                     'claim_containment_rate': len(full_claims) / len(claim_ids) if claim_ids else None,
                     'support_containment_rate': len(full_supports) / len(support_ids) if support_ids else None,
                     'claims_with_partial_links': len(partial),
                     'claims_without_full_chunk': len(claim_ids - full_claims),
                     'support_occurrences_without_full_chunk': len(support_ids - full_supports),
                     'citation_round_trips': citation_successes,
                     'citation_round_trip_rate': citation_successes / len(chunks) if chunks else None,
                     'deterministic_reproduction': deterministic})
    return rows
