"""User controls for kickstart pseudonymous telemetry."""

import json

import typer

from src.model.dto.telemetry import EffectiveTelemetry, TelemetryState, TelemetrySuppressionReason
from src.telemetry.config import posthog_settings_from_configuration
from src.telemetry.policy import resolve_telemetry
from src.telemetry.state import TelemetryStateStore
from src.utils.errors import TelemetryStateError


telemetry_app = typer.Typer(help="Inspect and control default-on pseudonymous telemetry.")


def _state_store() -> TelemetryStateStore:
    return TelemetryStateStore.from_environment()


@telemetry_app.command("status")
def telemetry_status(
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable telemetry status."),
) -> None:
    """Show persisted consent, delivery configuration, identity, and state location."""
    store = _state_store()
    try:
        state = store.read()
        effective = resolve_telemetry(store, state=state)
        consent = state.consent.value
    except TelemetryStateError:
        state = TelemetryState()
        effective = EffectiveTelemetry(
            enabled=False,
            reason=TelemetrySuppressionReason.INVALID_STATE,
            anonymous_id=None,
        )
        consent = "invalid"
    payload = {
        "anonymous_id": str(state.anonymous_id) if state.anonymous_id is not None else None,
        "consent": consent,
        "delivery_configured": posthog_settings_from_configuration() is not None,
        "effective": effective.enabled,
        "reason": effective.reason.value,
        "state_file": str(store.path),
    }
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True))
        return
    typer.echo(f"consent: {payload['consent']}")
    typer.echo(f"delivery-configured: {'yes' if payload['delivery_configured'] else 'no'}")
    typer.echo(f"effective: {'enabled' if effective.enabled else 'disabled'}")
    typer.echo(f"reason: {payload['reason']}")
    typer.echo(f"anonymous-id: {payload['anonymous_id'] or 'not-created'}")
    typer.echo(f"state-file: {payload['state_file']}")


@telemetry_app.command("enable")
def telemetry_enable() -> None:
    """Persist enablement and create an identity only when needed."""
    try:
        state = _state_store().enable()
    except TelemetryStateError as exc:
        _exit_with_state_error(exc)
    typer.echo("Telemetry enabled.")
    typer.echo(f"anonymous-id: {state.anonymous_id}")


@telemetry_app.command("disable")
def telemetry_disable() -> None:
    """Explicitly opt out while retaining any existing identity."""
    try:
        state = _state_store().disable()
    except TelemetryStateError as exc:
        _exit_with_state_error(exc)
    typer.echo("Telemetry disabled.")
    typer.echo(f"anonymous-id: {state.anonymous_id or 'not-created'}")


@telemetry_app.command("reset-id")
def telemetry_reset_id() -> None:
    """Rotate an existing ID for future events without deleting history."""
    try:
        result = _state_store().reset_id()
    except TelemetryStateError as exc:
        _exit_with_state_error(exc)
    if result.previous_id is None:
        typer.echo("No telemetry ID exists; nothing was changed.")
        return
    typer.echo(f"previous-anonymous-id: {result.previous_id}")
    typer.echo(f"anonymous-id: {result.current_id}")
    typer.echo("Historical events are not deleted; request deletion separately using the previous ID.")


def _exit_with_state_error(error: TelemetryStateError) -> None:
    typer.echo(f"Telemetry state error: {error}", err=True)
    raise typer.Exit(code=1) from error
