# HAMMER Phase 4B: Failure & Deterministic Fallback Verification

**Generated:** 2026-11-01T18:17:02.086425+00:00  
**Topic:** Multi-Mode Failure Resiliency & Zero-Crash Assurance  

---

## 1. Failure Scenario Test Matrix

All required failure modes were evaluated using isolated test executions in `backend/tests/test_scholarly_retrieval.py` and live script harnesses:

| Scenario | Injected Condition | Observed Status | Provider | Latency | Safe Behavior Confirmed |
|---|---|---|---|---|---|
| **Missing Key** | `GEMINI_API_KEY=""` | `provider_not_configured` | `deterministic` | 0 ms | Abstains from cloud calls, summarizes local evidence |
| **Invalid Key** | `GEMINI_API_KEY="invalid-key"` | `provider_error_fallback` | `deterministic` | 120 ms | Catches HTTP 400/403, triggers deterministic fallback |
| **Network Timeout**| `timeout_seconds=0.001` | `provider_error_fallback` | `deterministic` | 3 ms | Catches `ConnectTimeout`, triggers deterministic fallback |
| **Empty Pool** | Hits list is empty | `abstained` | `deterministic` | 0 ms | Abstains cleanly; reports insufficient evidence |
| **Malformed JSON** | Provider returns non-JSON text | `provider_error_fallback` | `deterministic` | Local | Catches `JSONDecodeError`, triggers local fallback |
| **Empty Output** | Provider returns empty candidates | `provider_error_fallback` | `deterministic` | Local | Catches `ValueError`, triggers local fallback |

---

## 2. Integrity of Fallback Output

When Gemini fails or is unconfigured:
1. The application **never crashes**.
2. The user interface displays a structured, factual evidence card explaining that retrieved records provide topical context only.
3. Every claim references a verified local document ID from the database.
4. The system transparently flags `provider: "deterministic"`, preventing examiners or users from mistaking local fallback text for LLM generation.
