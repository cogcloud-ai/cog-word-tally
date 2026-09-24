---
type: cog [0.1]
name: cog-word-tally
description: Tally word frequencies across supplied texts, accumulating prior counts.
version: "0.1.0"
manifest: cog.yaml
manifest_schema: openteams/cog-manifest [0.1]
---

# Word tally

This pure code Cog serves an Op accumulating word frequencies across steps. Its distinct unit of work is one deterministic tally of a finite supplied bundle. The Op reuses it by passing a previous result's counts as the next invocation's prior_counts. There is no persistent state and the input is not mutated.

Identity: openteams/cog-word-tally. Owner: trent@openteams.com. License: Apache-2.0. Produces: word_tally. Kind: code. Locality: local. Model requirements: none.

## Contract

Input and output are defined by context/input-schema.json and context/output-schema.json. Input requires a non-empty texts array of strings. prior_counts is optional and defaults to an empty object. Prior keys are taken verbatim, including empty strings, uppercase keys and keys containing punctuation; zero entries remain present. Counts must be non-negative integers; booleans are rejected.

Each text is independently lowercased with Python str.lower(), then tokenized with re.findall("[a-z0-9]+(?:'[a-z0-9]+)*", text.lower()). Internal ASCII apostrophes remain in tokens, digits are word characters and other punctuation separates tokens. There is no stemming, stop-word removal or additional Unicode normalization. Observed counts are added to a copy of prior_counts. total_words is the sum of every resulting count, including prior entries. authority_use is always []. The bundle is the sole grounding source.

Valid input always yields a complete result, including empty or punctuation-only texts. With no tokens and no prior counts, the output is {"counts": {}, "total_words": 0, "authority_use": []}. With prior counts and no tokens, the prior entries are preserved. Invalid input yields structured schema or contract problems and no partial tally payload; validation tolerates schema-invalid values without throwing. Empty text strings do not cause abstention.

Unsupported work includes reading files, networking, subprocesses, executing supplied text, external effects, runtime models, training, grants, third-party dependencies, persistent accumulation, alternative tokenization and partial answers for invalid inputs. Task logic uses only Python's standard library and Smith's required cog_core.problem API.

Prohibitions, exactly as accepted:

- execute_actions
- send_external_message

## Host API and reuse

src/task_logic.py exports check_input(bundle), run(bundle, grant, journal), and check_output(payload, bundle). Validators return lists of cog_core.problem values. run returns (payload, problems), with the real output object on success and (None, problems) on invalid input. Smith supplies the envelope and invokes the declared run task with --bundle. The grant and journal arguments are unused. Smith owns all other src modules and package formatting.

The surrounding Op must supply independent Guards for its own authorization and boundary policies and separate acceptance Gates for its workflow results. This Cog does not implement those independent responsibilities. Package checks and this Cog's self-validation are not independent Guards or acceptance Gates.

## Acceptance criteria

- tokenization: The exact regex after str.lower() preserves internal apostrophes and digits. The specified Don't/42/foo-bar/rock'n'roll/café example must match the accepted counts.
- accumulation: Prior entries are preserved exactly, observed counts are added rather than replaced, zero entries remain and input stays unchanged. The specified Cat example yields cat 5, Cat 4, dog 1, empty-key 2 and unused 0.
- totals: total_words equals sum(counts.values()); the accumulation example totals 12. Omitted and empty prior_counts behave identically.
- empty: Empty and punctuation-only texts yield empty counts and zero without prior counts, or preserve supplied prior counts and their total.
- invalid_input: Non-object bundles, missing/empty/non-array texts, non-string elements, malformed prior_counts, negative/fractional/string/boolean counts and unexpected top-level properties produce problems and no partial tally.
- no_side_effects: Every successful result has authority_use []. No file, network, subprocess, execution, model, grant or persistent-state use occurs. Executable-looking text remains ordinary tokenizable data.

## Deterministic tests

Run python -m unittest discover -s tests from the package root in Smith's declared environment. Tests add src to sys.path themselves. They cover happy, insufficient-input, adversarial, boundary and schema-invalid cases, exact output validation, input immutability, repeated use and effect boundaries. No model fixtures are needed for this code Cog. Source and tests are supplied here without any claim that they have been executed.
