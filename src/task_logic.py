"""Pure, deterministic word tally for the Smith code-task API."""

import re


def _count_problems(value, label):
    import cog_core

    problems = []
    if not isinstance(value, dict):
        return [cog_core.problem(label, 'Expected an object mapping strings to non-negative integers.')]
    for key, count in value.items():
        if not isinstance(key, str):
            problems.append(cog_core.problem(label, 'Every count key must be a string.'))
        if type(count) is not int or count < 0:
            problems.append(cog_core.problem(label, 'Every count must be a non-negative integer; booleans are invalid.'))
    return problems


def check_input(bundle):
    import cog_core

    if not isinstance(bundle, dict):
        return [cog_core.problem('input', 'Expected an object bundle.')]
    problems = []
    if set(bundle) - {'texts', 'prior_counts'}:
        problems.append(cog_core.problem('input.properties', 'Unexpected top-level properties.'))
    if 'texts' not in bundle:
        problems.append(cog_core.problem('input.texts', 'texts is required.'))
    else:
        texts = bundle['texts']
        if not isinstance(texts, list):
            problems.append(cog_core.problem('input.texts', 'texts must be an array.'))
        elif not texts:
            problems.append(cog_core.problem('input.texts', 'texts must contain at least one string.'))
        else:
            for text in texts:
                if not isinstance(text, str):
                    problems.append(cog_core.problem('input.texts', 'Every text must be a string.'))
    if 'prior_counts' in bundle:
        problems.extend(_count_problems(bundle['prior_counts'], 'input.prior_counts'))
    return problems


def _tally(bundle):
    counts = dict(bundle.get('prior_counts', {}))
    for text in bundle['texts']:
        for token in re.findall("[a-z0-9]+(?:'[a-z0-9]+)*", text.lower()):
            counts[token] = counts.get(token, 0) + 1
    return {'counts': counts, 'total_words': sum(counts.values()), 'authority_use': []}


def run(bundle, grant, journal):
    problems = check_input(bundle)
    if problems:
        return None, problems
    return _tally(bundle), []


def check_output(payload, bundle):
    import cog_core

    problems = check_input(bundle)
    if problems:
        return problems
    if not isinstance(payload, dict):
        return [cog_core.problem('output', 'Expected an object payload.')]
    if set(payload) != {'counts', 'total_words', 'authority_use'}:
        problems.append(cog_core.problem('output.properties', 'Exactly counts, total_words and authority_use are required.'))
    problems.extend(_count_problems(payload.get('counts'), 'output.counts'))
    total = payload.get('total_words')
    if type(total) is not int or total < 0:
        problems.append(cog_core.problem('output.total_words', 'total_words must be a non-negative integer; booleans are invalid.'))
    authority = payload.get('authority_use')
    if not isinstance(authority, list) or authority:
        problems.append(cog_core.problem('output.authority_use', 'authority_use must be an empty array.'))
    if problems:
        return problems
    expected = _tally(bundle)
    if payload['counts'] != expected['counts']:
        problems.append(cog_core.problem('output.grounding', 'counts must exactly preserve prior entries and add the specified token frequencies.'))
    if total != sum(payload['counts'].values()):
        problems.append(cog_core.problem('output.totals', 'total_words must equal the sum of counts.'))
    return problems
