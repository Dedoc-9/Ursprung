# SPDX-License-Identifier: AGPL-3.0-only
# DVSM verification gate. `make verify` runs every open-core + commercial suite as one gate.
# Cross-platform: the real logic lives in verify.py (so `python verify.py` works where make does not,
# e.g. PowerShell). PYTHONHASHSEED is forced inside verify.py's subprocess env.

PYTHON ?= python

.PHONY: verify verify-core verify-commercial demos clean

verify:            ## run ALL DVSM + commercial suites as one gate
	$(PYTHON) verify.py

verify-core:       ## open-core suites only
	$(PYTHON) verify.py core

verify-commercial: ## commercial suites only
	$(PYTHON) verify.py commercial

demos:             ## run the module demos (non-gating, illustrative)
	$(PYTHON) dvsm_reference.py
	$(PYTHON) coupling_audit.py
	$(PYTHON) invariant_ledger.py
	$(PYTHON) dvsm_backend.py
	$(PYTHON) commercial/kernel_auditor.py
	$(PYTHON) commercial/commercial_obligations.py
	$(PYTHON) commercial/binframe_adapter.py

clean:             ## remove caches and demo artifacts
	rm -rf __pycache__ commercial/__pycache__ commercial/_demo_*.bin
