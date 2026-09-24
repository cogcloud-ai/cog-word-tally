# cog-word-tally

Tally word frequencies across supplied texts, accumulating prior counts. A
pure-code Cog with no model, no network and no files: one deterministic tally
per invocation, reusable across Op steps by passing a result's `counts` back as
the next invocation's `prior_counts`.

See [COG.md](COG.md) for the work contract and
[BUILD-HANDOFF.json](BUILD-HANDOFF.json) for the accepted contract this package
was built from.

```sh
pixi install
pixi run test
pixi run run -- --bundle examples/sample-bundle.json
```

## Provenance

This package is the first Cog built end to end through
[op-cog-builder](https://github.com/cogcloud-ai/op-cog-builder) 0.2.0 with both
acceptance Gates: the contract was designed by cog-author from a brief and
explicitly accepted; the source was authored, materialized and verified; the
evaluator passed all six acceptance criteria; and the candidate was explicitly
accepted, bound to these digests:

| Digest | sha256 |
|---|---|
| contract | `9e07330f7c8964948cbc8b3727f37f725df983ac55d18ef19022cf24c731836d` |
| source | `8dde7e447d3b6570eb5480137f287425bf9543eedfc9c16adbc293660f36f61e` |
| package (as verified) | `5d68047ce5afd1d51bd938c1f67540bab3223f71ce876209197c3352bacb1450` |

The build record is
[live-gates-2026-09-23.md](https://github.com/cogcloud-ai/op-cog-builder/blob/main/docs/live-gates-2026-09-23.md).
It was a second run: the first candidate's task logic was identical, but its
authored test file asserted a wrong total, which the evaluator found; the
revision was built from that source with the finding as feedback. Authoring
used the ChatGPT provider; planning and review used the Claude provider.
Model-generated source and tests were independently reviewed before acceptance.
The files added for publication (this README, LICENSE, SECURITY.md,
CONTRIBUTING.md, `.gitignore`, the CI workflow and `pixi.lock`) are outside the
verified package digest, which covers the Cog's manifest, context, source and
tests.

The Smith-supplied machinery in `src/` (everything but `task_logic.py`) is
checked by hash by `smith check`.

## License

Copyright 2026 OpenTeams. Licensed under the [Apache License 2.0](LICENSE).
Third-party dependencies retain their own licenses and terms.

## Public preview

See the [suite guide](https://github.com/cogcloud-ai/cog-op-builder/blob/main/docs/repositories.md)
for repository roles, supported setup, and current limitations.
