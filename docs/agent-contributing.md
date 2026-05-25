# Agent Contributing

This file is for coding agents modifying kickstart.

## Operating Rules

- Do not refactor because a file is large.
- Refactor only for human/agent clarity or to address a weakly tested path.
- Do not change generated behavior without saying so and updating tests.
- Do not edit tests just to make a refactor pass.
- Do not commit reports, scratch files, or local idea notes.

## Before Editing

Run:

```bash
git status --short
make lint
make typecheck
make tests
```

If touching generation, create a before-output fixture in `/tmp` and compare it after the change.

For the TypeScript Cloudflare Worker scaffold, keep the committed fixture in sync:

- fixture: `tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker`
- drift test: `tests/integration/test_scaffold_golden.py`

Regenerate with:

```bash
tmpdir=$(mktemp -d)
poetry run kickstart create service hello-worker --lang typescript --runtime cloudflare-workers --root "$tmpdir"
rm -rf tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker
mkdir -p tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker
cp -R "$tmpdir/hello-worker/." tests/fixtures/golden/service-hello-worker-typescript-cloudflare-worker/
```

Then run:

```bash
PYTHONPATH=$(pwd) poetry run pytest tests/integration/test_scaffold_golden.py
```

## Preferred Shape

Generators should read like:

1. normalize input into a spec
2. select a stack profile
3. get directory and template plans
4. execute the plan
5. run narrow language/runtime setup

Avoid adding new untyped dictionaries when a dataclass or existing typed config fits.

## Final Evidence

Report:

- files changed
- behavior changed or unchanged
- test command output
- generated-output diff result, when relevant

For release/build changes, also report `make package` and `make binary` results when they were run locally.
