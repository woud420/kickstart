# Pseudonymous CLI telemetry contract

This contract governs the default-on product telemetry emitted by the kickstart CLI. It is a data-minimization boundary, not a promise that a stable identifier is anonymous: a durable random identifier correlates events over time and is therefore pseudonymous.

## Product questions

The allowlisted events exist only to answer these questions:

1. Which project kinds, languages, runtimes, and optional scaffold capabilities are useful?
2. Which supported combinations are most common?
3. Which coarse failure categories prevent scaffold creation?
4. Which supported install artifact kinds are used, and how often is PATH integration requested or already present?
5. Do CLI-managed installs and upgrades succeed, and where do checksum or update flows fail?
6. Which released CLI versions and packaged platforms are still active?
7. Is the event contract useful enough to justify maintaining telemetry or a first-party relay?

Telemetry is deliberately lossy and spoofable. It is product feedback, not billing, audit, security, identity, unique-person, or authoritative usage evidence.

## Consent and effective enablement

- Telemetry is enabled by default for ordinary installed CLI runs when delivery is configured.
- Missing state represents the default-enabled policy, not explicit consent. Merely checking status does not create state or an identity.
- The first eligible event with a configured sink lazily creates and persists a random UUIDv4 unless explicit enablement already created one. The ID remains stable across CLI upgrades.
- `kickstart telemetry enable` reverses a persisted disable and creates an identity if one does not exist.
- `kickstart telemetry disable` persists opt-out and retains an existing ID.
- `kickstart telemetry status` is strictly read-only: it does not create or rewrite state, initialize an ID, or send an event. It displays the current ID when one exists.
- `kickstart telemetry reset-id` rotates an existing ID for future events and reports the previous ID. Rotation does not delete historical events.

Hard process-level suppressions override both the default and persisted enablement in this order:

1. `DO_NOT_TRACK=1`
2. `KICKSTART_TELEMETRY_DISABLED=1`
3. a truthy `CI` environment variable
4. pytest via `PYTEST_CURRENT_TEST`
5. `KICKSTART_EVAL=1`
6. execution from the kickstart source checkout

A deliberate development-only verification may bypass the source-checkout guard with `KICKSTART_TELEMETRY_ALLOW_DEVELOPMENT=1`; it does not bypass a persisted disable or any other hard suppression.

To prevent an installer-invoked event before a preference can exist, set either
hard suppression on that invocation:

```bash
KICKSTART_TELEMETRY_DISABLED=1 ./kickstart-macos-arm64-py3.14/kickstart install --update-path
# Or use the standard environment-wide preference:
DO_NOT_TRACK=1 ./kickstart-macos-arm64-py3.14/kickstart install --update-path

# The same controls are inherited by the downloaded binary in the quick installer:
curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh \
  | KICKSTART_TELEMETRY_DISABLED=1 bash
```

These environment settings apply to the current process. Run
`kickstart telemetry disable` to persist the preference for later commands.

## Identity and persistence

State is stored separately from repository configuration and the replaceable application payload:

```text
${XDG_CONFIG_HOME:-~/.config}/kickstart/telemetry.json
```

The versioned document contains only `schema_version`, `consent`, and an optional random UUIDv4 `anonymous_id`. Missing state is a valid default-enabled state but has no identity. An explicit disable may be persisted without creating an ID. Explicit enablement creates the ID immediately; otherwise, when delivery is configured, the first eligible event initializes it before capture. If persistence fails, no event is sent. The ID is never derived from a username, hostname, MAC address, Git configuration, path, email address, project, repository, or PostHog value. Atomic writes, serialized initialization, and user-only permissions are used where the platform supports them.

Malformed, unreadable, busy, symlinked, or unwritable state fails closed. A genuinely missing state file follows the default-enabled behavior above. Telemetry failures never change the output, exit status, generated files, or deterministic behavior of another command.

## Event allowlist

Exactly three event names are allowed:

- `scaffold_create_completed`
- `cli_install_completed`
- `cli_upgrade_completed`

At most one terminal event may be attempted for an eligible invocation that reaches the corresponding command boundary. Parser failures that occur before the command function starts are outside this boundary. `cli_install_completed` means only an invocation of `kickstart install`, including the PATH-configuration invocation made by the shell installer when applicable; the shell download/copy itself, `pip`, `pipx`, package managers, and manual copies are not independently counted. `cli_upgrade_completed` means only `kickstart upgrade`. These events therefore do not measure universal installation or upgrade totals.

The provider-neutral envelope contains only:

- `event_id`: random UUIDv4 for deduplication
- `anonymous_id`: the persisted random UUIDv4
- `occurred_at`: UTC event time
- `name`: the allowlisted event name
- `properties`: the closed property object below

The exact closed property set for `scaffold_create_completed` is:

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

The six common lifecycle properties for install and upgrade events are exactly:

- `cli_version`
- `outcome`
- `error_category`
- `duration_bucket`
- `platform`
- `architecture`

The exact closed property set for `cli_install_completed` is those six common properties plus:

- `artifact_kind`: `single_file`, `onedir`, or `unknown`
- `path_update_requested`: boolean
- `already_on_path`: boolean

Its `outcome` is one of `success`, `no_change`, `partial_success`, `failed`, or `cancelled`. Its `error_category` is one of `none`, `interrupted`, `source_missing`, `destination_conflict`, `permission_denied`, `path_update`, `filesystem_error`, `expected_error`, or `unexpected_error`.

The exact closed property set for `cli_upgrade_completed` is those six common properties plus:

- `target_version`: a stable semantic version or `unknown`
- `checksum_status`: `verified`, `not_published`, `failed`, or `not_reached`

Its `outcome` is one of `updated`, `already_current`, `failed`, or `cancelled`. Its `error_category` is one of `none`, `interrupted`, `release_lookup`, `invalid_release_metadata`, `unsupported_platform`, `archive_missing`, `download`, `checksum_fetch`, `checksum_mismatch`, `archive_extraction`, `installation`, or `unexpected_error`.

No other event or property is permitted. In particular, uninstall does not emit an event. Values that are not in these fixed sets are omitted or normalized to an allowed fallback; raw values are never serialized.

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

Every PostHog event sets `$process_person_profile` to `false`. The adapter never identifies, aliases, groups, or sets person properties. GeoIP enrichment is not disabled: because phase one connects directly, PostHog receives the HTTPS connection and may process its source IP and add provider-derived geographic properties. These connection and provider-derived fields are outside the CLI-authored property allowlist and are accepted for the initial deployment.

Direct public capture can be spoofed. Provider, destination, or token changes require upgraded direct clients, and there is no first-party server kill switch in phase one. A later first-party relay may replace the sink without changing event producers, consent, or identity.

Official wheel, source-distribution, and standalone-binary artifacts embed the public capture token from the `POSTHOG_PUBLIC_CUSTOMER_API_TOKEN` GitHub Actions secret during trusted build jobs. The secret prevents accidental disclosure in source and build logs; it does not make the token confidential after publication. Anyone can recover a public token from a distributed client, and token rotation requires newly built clients.

For local development and source installations, `POSTHOG_PUBLIC_CUSTOMER_API_TOKEN` may be exported from an ignored `.env` into the process. An explicit process value overrides artifact configuration, including failing closed when that override is malformed. The CLI reads only the already-exported process environment and never auto-loads a current repository's `.env`, because kickstart runs inside arbitrary repositories and repository content must not influence telemetry routing or consent. A missing artifact token and missing or malformed runtime token silently select a no-op sink. A valid token configures delivery but never overrides a persisted disable or process-level suppression. The numeric `POSTHOG_PROJECT_ID` is not read, embedded, or included in capture payloads.

## Delivery and retention

Delivery is best-effort: one request, a small timeout, no retries, and no local raw-event queue. State, mapping, serialization, and transport exceptions are contained within telemetry.

The initial account uses PostHog Cloud US on the Free plan with its current default one-year event retention. Retention is an account setting and must be rechecked before release.

Historical deletion is handled on request for a supplied pseudonymous ID. `status` exposes the current ID; `reset-id` reports the previous one. Rotation affects future events only. The deletion workflow must explicitly delete events, must be verified using a synthetic ID, and must never expose the required personal API key. The public deletion-request contact channel remains a release TODO.
