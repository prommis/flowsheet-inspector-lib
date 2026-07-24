# Diagnostic Evidence Routing

Use this guide to distinguish a complete run from a partial run without blocking the user-friendly diagnostic loop.

## Named flowsheet

A named flowsheet request means: run it first. Execute the complete registered step sequence once in a fresh process and collect all evidence produced.

Classify the outcome as:

- **Complete with IPOPT and diagnostics:** a structured solver result exists and the standard structural and numerical reports ran.
- **Complete without IPOPT:** the registered sequence completed but did not expose a solver result. Explain that no IPOPT result was available and show the diagnostics that exist.
- **Partial with model evidence:** import/build/initialization/solve stopped, but the runner retained a model. Explain where the run stopped, label the evidence as partial, run structural diagnostics, then run the safe missing-value and bounds checks on the retained state.
- **No model evidence:** the run stopped before a model was available. Give the concise phase and exception message needed to explain why IPOPT and DiagnosticsToolbox could not run. Do not pretend this is an IPOPT failure.

Runner and Python exceptions are boundary evidence: they explain why the desired solver or diagnostic evidence was not reached. They may be shown briefly when necessary, but they are not automatically the model's root cause.

Diagnostics from a partial model can include temporary initialization fixes and unfinished state. Treat broad structural warnings from that state as clues, not confirmed causes.

An explicit component finding that includes a current value and its bounds is stronger evidence than a broad structural or potential-evaluation warning from a partial model. Use the flowsheet source only to confirm the reported component and specification.

## Pasted output

Classify pasted evidence as IPOPT, DiagnosticsToolbox, both, or neither.

- For IPOPT, use `ipopt-guide.md`.
- For DiagnosticsToolbox, use `diagnostics-guide.md`.
- For both, explain the solver result first and use DiagnosticsToolbox to locate the likely model issue.
- For neither, state that the pasted text is not IPOPT or DiagnosticsToolbox output and ask for the named flowsheet or the relevant solver/diagnostic section only when needed.

Do not run a named flowsheet merely to repeat pasted output unless the user also asks for runtime verification.

## Evidence priority

Use the standard reports to choose focused checks. Rank conclusions in this order:

1. Structured solver result, exact IPOPT output, or exact runner exception from the current run.
2. Explicit component findings from a report-supported focused method, including current values and bounds.
3. Model code that confirms the reported component and specification.
4. Broad DiagnosticsToolbox structural or numerical warnings, labeled with their evidence scope.
5. Potential warnings and cautions that do not identify a current violation.

Keep complete evidence internally. Present only what the user needs for the next decision.
