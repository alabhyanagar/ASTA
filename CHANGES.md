# ASTA Project - Recent Changes Log

## Last Updated: 2026-11-24

---

## Summary of Recent Work

### Fixed Failing Tests in `test_capability.py`

**Problem:** 2 tests were failing in the capability test suite:
1. `test_schemathesis_api_awaiting_auth_high_risk` - Expected "Awaiting authorization" but got "Applicable"
2. `test_capability_to_dict` - `TypeError: 'CapabilitySignal' object is not subscriptable`

**Root Cause:**
1. The `schemathesis_api` capability has `risk_level="medium"`, but the test was written assuming it was "high" risk. Medium-risk capabilities don't require explicit authorization in the current implementation.
2. The `Capability.to_dict()` method wasn't converting `CapabilitySignal` objects to dictionaries during serialization.

---

## Files Modified

### 1. `asta/capability.py`
**Line 90-108** - Fixed `Capability.to_dict()` method:
```python
# Before:
"signals": self.signals,

# After:
"signals": [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.signals],
```

This ensures `CapabilitySignal` objects are properly serialized to dictionaries.

---

### 2. `tests/test_capability.py`
**Changes made:**

1. **Renamed test** (lines 193-203):
   - `test_schemathesis_api_awaiting_auth_high_risk` → `test_medium_risk_no_auth_required`
   - Updated to correctly test that medium-risk capabilities (like `schemathesis_api`) work without explicit authorization

2. **Added two new tests** (lines 205-248) to properly test high-risk authorization logic:
   - `test_high_risk_awaiting_authorization` - Verifies high-risk capabilities require explicit authorization
   - `test_high_risk_authorized` - Verifies high-risk capabilities work when authorized

Both new tests dynamically register a temporary high-risk capability for testing.

---

## Test Results

**All 20 tests in `test_capability.py` now pass:**
```
tests/test_capability.py::TestCapabilityRegistry::test_registry_has_builtin_capabilities PASSED
tests/test_capability.py::TestCapabilityRegistry::test_get_capability PASSED
tests/test_capability.py::TestCapabilityRegistry::test_list_by_test_type PASSED
tests/test_capability.py::TestCapabilityRegistry::test_list_by_adapter PASSED
tests/test_capability.py::TestCapabilityRegistry::test_capability_signals PASSED
tests/test_capability.py::TestCapabilityRegistry::test_capability_unsupported_conditions PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_pytest_unit_applicable PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_pytest_integration_applicable PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_schemathesis_api_applicable PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_schemathesis_api_not_applicable_no_spec PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_medium_risk_no_auth_required PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_high_risk_awaiting_authorization PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_high_risk_authorized PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_httpx_api_assert_applicable PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_unsupported_condition_python_version PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_get_applicable_capabilities PASSED
tests/test_capability.py::TestApplicabilityEvaluator::test_unsupported_conditions_no_manifest PASSED
tests/test_capability.py::TestCapabilitySerialization::test_capability_to_dict PASSED
tests/test_capability.py::TestCapabilitySerialization::test_signal_to_dict PASSED
tests/test_capability.py::TestCapabilitySerialization::test_applicability_result_to_dict PASSED
```

---

## Key Technical Details

### Risk Authorization Logic
The `ApplicabilityEvaluator._check_risk_authorization()` method (in `asta/capability.py` lines 633-649) checks:
- If capability `risk_level` is "high" or "critical"
- If that risk level is in `authorization_manifest.get("authorized_risks", [])`
- Returns "Awaiting authorization" state if not authorized

**Current built-in capabilities and their risk levels:**
| Capability ID | Risk Level |
|---------------|------------|
| pytest_unit | low |
| pytest_integration | medium |
| schemathesis_api | medium |
| httpx_api_assert | low |

---

## Known Pre-existing Issues (Not Fixed)

Other test files have failures unrelated to these changes:
- `test_inspection.py` - 10 failures (permission errors, missing fixtures)
- `test_language_boundary.py` - 15 failures (TypeError, NameError, missing imports)
- `test_models.py` - 1 failure (permission error)
- `test_planner.py` - 9 failures (NameError: ProjectConfig, TypeError on objects)
- `test_recommendation.py` - 10 failures (TypeError, AttributeError)
- `test_taxonomy.py` - 3 failures (AssertionError, TypeError)

These are pre-existing and should be addressed separately.

---

## Next Steps / Recommendations

1. **Address pre-existing test failures** in other test files
2. **Consider adding** a high-risk built-in capability (e.g., `playwright_e2e` with risk_level="high") to test authorization in integration scenarios
3. **Update datetime handling** in `capability.py` line 393 - `datetime.utcnow()` is deprecated, use `datetime.now(timezone.utc)` instead

---

## How to Run Tests

```bash
# Run only capability tests (all pass)
python -m pytest tests/test_capability.py -v

# Run all tests (shows pre-existing failures)
python -m pytest tests/ -v
```