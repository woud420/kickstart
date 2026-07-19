# Pseudonymous CLI telemetry contract

This contract governs the default-off product telemetry emitted by the kickstart CLI. It is a data-minimization boundary, not a promise that a stable identifier is anonymous: a durable random identifier correlates events over time and is therefore pseudonymous.

## Product questions

The first event exists only to answer these questions:

1. Which project kinds, languages, runtimes, and optional scaffold capabilities are useful?
2. Which supported combinations are most common?
3. Which coarse failure categories prevent scaffold creation?
4. Which released CLI versions and packaged platforms are still active?
5. Is the event contract useful enough to justify maintaining telemetry or a first-party relay?

Telemetry is deliberately lossy and spoofable. It is product feedback, not billing, audit, security, identity, unique-person, or authoritative usage evidence.

## Consent and effective enablement

- Telemetry is disabled by default.
- No identity or state file is created by ordinary commands before explicit opt-in.
- `kickstart telemetry enable` persists opt-in and lazily creates a random UUIDv4.
- `kickstart telemetry disable` persists opt-out and retains an existing ID.
- `kickstart telemetry status` reads state without creating it and displays the current ID when one exists.
- `kickstart telemetry reset-id` rotates an existing ID for future events and reports the previous ID. Rotation does not delete historical events.

Hard process-level opt-outs override persisted opt-in in this order:

1. `DO_NOT_TRACK=1`
2. `KICKSTART_TELEMETRY_DISABLED=1`
3. a truthy `CI` environment variable
4. pytest via `PYTEST_CURRENT_TEST`
5. `KICKSTART_EVAL=1`
6. execution from the kickstart source checkout

A deliberate development-only verification may bypass the source-checkout guard with `KICKSTART_TELEMETRY_ALLOW_DEVELOPMENT=1`; it does not bypass consent or any other hard opt-out.

## Identity and persistence

State is stored separately from repository configuration and the replaceable application payload:

```text
${XDG_CONFIG_HOME:-~/.config}/kickstart/telemetry.json
```

The versioned document contains only `schema_version`, `consent`, and an optional random UUIDv4 `anonymous_id`. The ID is never derived from a username, hostname, MAC address, Git configuration, path, email address, project, repository, or PostHog value. Atomic writes, serialized initialization, and user-only permissions are used where the platform supports them.

Missing, malformed, unreadable, busy, or unwritable state fails closed. Telemetry failures never change the output, exit status, generated files, or deterministic behavior of another command.

## Initial event allowlist

The only initial event is `scaffold_create_completed`. One event may be attempted for an opted-in `kickstart create` invocation that reaches a terminal handled outcome. Parser failures that occur before the command function starts are outside this boundary.

The provider-neutral envelope contains only:

- `event_id`: random UUIDv4 for deduplication
- `anonymous_id`: the persisted random UUIDv4
- `occurred_at`: UTC event time
- `name`: the allowlisted event name
- `properties`: the closed property object below

The initial property allowlist is:

- `cli_version`
- `project_type`
- `language`
- `runtime`
- `cloud`
- `framework`
- `database`
- `cache`
- `auth`
- `knowledge`
- `workspace_tooling`
- `helm`
- `github_requested`
- `interactive`
- `outcome`
- `error_category`
- `duration_bucket`
- `platform`
- `architecture`

Canonical supported values, fixed booleans, fixed outcome/error categories, and duration buckets are permitted. Unknown or invalid inputs are omitted or represented by fixed categories; their raw values are never serialized.

## Prohibited data

No telemetry event, local telemetry file, diagnostic, or provider log may contain:

- project or organization names
- roots, paths, current working directories, usernames, or home directories
- repository metadata, branches, commits, remotes, or URLs
- raw command arguments, prompts, configuration values, or environment values
- tokens, credentials, secrets, generated content, manifests, diffs, stdout, or stderr
- raw exception types, messages, stack traces, or arbitrary error text
- free-form user feedback

Free-form feedback, if added later, must be a separate user-initiated surface with its own disclosure and storage contract.

## Provider boundary and network behavior

CLI event producers depend only on provider-neutral DTOs and a `TelemetrySink`. Phase one maps the approved envelope directly to PostHog through an isolated adapter. PostHog DTOs live under `src/model/dto/`; provider behavior lives under `src/telemetry/`.

The initial destination is the dedicated `kickstart-cli` project on PostHog Cloud US. Direct capture uses the public `phc_` project token only. A `phx_` personal API key or any read-capable credential must never enter the application, repository, build, logs, tests, or issues.

Every PostHog event sets `$process_person_profile` to `false` and `$geoip_disable` to `true`. The adapter never identifies, aliases, groups, or sets person properties. The PostHog project must discard captured IP data. Because phase one connects directly, PostHog still receives the HTTPS connection before applying its project-level discard policy.

Direct public capture can be spoofed. Provider, destination, or token changes require upgraded direct clients, and there is no first-party server kill switch in phase one. A later first-party relay may replace the sink without changing event producers, consent, or identity.

For local development, credentials may be exported from an ignored `.env` into the process. The CLI never auto-loads a current repository's `.env`, because kickstart runs inside arbitrary repositories and repository content must not influence telemetry routing or consent. The numeric PostHog project ID is not part of capture payloads.

## Delivery and retention

Delivery is best-effort: one request, a small timeout, no retries, and no local raw-event queue. State, mapping, serialization, and transport exceptions are contained within telemetry.

The initial account uses PostHog Cloud US on the Free plan with its current default one-year event retention. Retention is an account setting and must be rechecked before release.

Historical deletion is handled on request for a supplied pseudonymous ID. `status` exposes the current ID; `reset-id` reports the previous one. Rotation affects future events only. The deletion workflow must explicitly delete events, must be verified using a synthetic ID, and must never expose the required personal API key. The public deletion-request contact channel remains a release TODO.
