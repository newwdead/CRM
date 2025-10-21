# ADR-0002: Duplicate Detection Strategy

**Status:** Accepted  
**Date:** 2025-10-20  
**Deciders:** Development Team  
**Technical Story:** Implement automatic duplicate detection

## Context

Users manually managing hundreds of business cards need automatic detection of duplicate contacts to maintain data quality. Manual detection is:
- Time-consuming
- Error-prone
- Inconsistent

## Decision

Implement fuzzy matching-based duplicate detection using:

1. **Algorithm:** Weighted similarity scoring
2. **Library:** `fuzzywuzzy` with `python-Levenshtein`
3. **Approach:** Field-by-field comparison with weights
4. **Threshold:** Configurable (default 75%)

### Similarity Weights

```python
FIELD_WEIGHTS = {
    'email': 0.30,        # Highest - unique identifier
    'phone': 0.25,        # High - unique identifier
    'full_name': 0.20,    # Medium - can vary
    'company': 0.15,      # Medium - context
    'position': 0.10,     # Low - generic
}
```

### Detection Modes

1. **Automatic:** On contact creation
2. **Manual:** Bulk scan via admin panel
3. **Scheduled:** Celery task (future)

## Rationale

**Why Fuzzy Matching?**
- Handles typos and variations
- Name transliteration (Cyrillic ↔ Latin)
- Phone format normalization
- Reasonable performance for 1000s of contacts

**Why Not Exact Matching?**
- Misses near-duplicates
- Can't handle data entry errors

**Why Not Machine Learning?**
- Overkill for current scale
- Requires training data
- Higher computational cost
- Harder to explain to users

## Consequences

### Positive
- Automatic detection saves time
- Configurable threshold per organization
- Field-level similarity helps merge decisions
- Works with existing data

### Negative
- False positives at low thresholds
- Performance impact on large datasets
- Requires `fuzzywuzzy` + `python-Levenshtein` dependencies

### Performance

**Benchmarks:**
- 100 contacts: ~50ms
- 1,000 contacts: ~500ms
- 10,000 contacts: ~15s (needs optimization)

**Optimization Strategies:**
- Index common fields
- Cache phonetic encodings
- Batch processing via Celery
- Skip comparison if key fields missing

## Implementation

```python
def calculate_contact_similarity(contact1, contact2):
    """Calculate weighted similarity between contacts"""
    scores = {}
    total_score = 0.0
    total_weight = 0.0
    
    for field, weight in FIELD_WEIGHTS.items():
        val1 = contact1.get(field)
        val2 = contact2.get(field)
        
        if val1 and val2:
            score = calculate_field_similarity(val1, val2)
            scores[field] = score
            total_score += score * weight
            total_weight += weight
    
    final_score = total_score / total_weight if total_weight > 0 else 0
    return final_score, scores
```

## Alternatives Considered

### 1. Exact Matching Only
**Rejected:** Misses too many duplicates

### 2. Phonetic Matching (Soundex/Metaphone)
**Considered:** Good for names, but doesn't handle emails/phones

### 3. Elasticsearch Fuzzy Search
**Rejected:** Additional infrastructure, overkill

### 4. Dedupe.io Library
**Considered:** More powerful but requires training

### 5. Custom ML Model
**Rejected:** Too complex for current needs

## Validation

**Test Cases:**
- ✅ Identical contacts → 1.0 score
- ✅ Different case → High score
- ✅ Typos → Medium-high score
- ✅ Different contacts → Low score
- ✅ Phone format variations → Normalized

## Future Improvements

1. **Machine Learning:**
   - Learn from user merge/ignore decisions
   - Adaptive thresholds

2. **Performance:**
   - Locality-sensitive hashing (LSH)
   - Blocking/indexing strategies

3. **Smart Merging:**
   - Suggest best merge candidates
   - Auto-merge high confidence duplicates

## References

- [fuzzywuzzy Documentation](https://github.com/seatgeek/fuzzywuzzy)
- Implementation: `/backend/app/duplicate_utils.py`
- Tests: `/backend/app/tests/test_duplicate_utils.py`
- API: `/backend/app/api/duplicates.py`

