"""Order-path safety guard (kanban t_03f5687f, 2026-10-09).

Hard account guard shared by EVERY IBKR order-placing path (TWS sessions via
ib_service, Client Portal via ib_web_service, and the /api/ib/place-order
route):

- Orders may ONLY reach the allowed account (default DUP825942, overridable
  via IBKR_ALLOWED_ACCOUNT for a future account migration).
- Any other account — requested or connected — is refused unless the user has
  explicitly enabled live trading with IBKR_LIVE_TRADING_ENABLE=true in the
  backend environment (backend/.env, loaded by start.sh; requires a backend
  restart, which is deliberate — enabling live is an ops action, not a
  request parameter).
- An unknown connected account (None) is refused: fail closed.

Background: three proven incidents (2026-08-25, 2026-09-23, 2026-09-28) of
untagged/defaulted orders hitting the real UAT account DUP825942.
"""
import os

ALLOWED_ACCOUNT = os.environ.get("IBKR_ALLOWED_ACCOUNT", "DUP825942")

_TRUE_VALUES = {"1", "true", "yes", "on"}


def live_trading_enabled() -> bool:
    """User-set live-enable flag. Only the backend environment can set this —
    it is never accepted from request payloads."""
    return os.environ.get("IBKR_LIVE_TRADING_ENABLE", "").strip().lower() in _TRUE_VALUES


def requested_account_guard_error(requested_account=None):
    """Endpoint-layer guard: refuse when the caller NAMES an account other
    than the allowed one. The connected-account check happens at the service
    layer, where the session is known."""
    if live_trading_enabled():
        return None
    if requested_account is not None and str(requested_account).strip() \
            and str(requested_account).strip() != ALLOWED_ACCOUNT:
        return (
            f"account guard: requested account '{requested_account}' is not the "
            f"allowed account {ALLOWED_ACCOUNT} — order refused "
            f"(set IBKR_LIVE_TRADING_ENABLE=true in backend/.env to enable other accounts)"
        )
    return None


def account_guard_error(connected_account=None, requested_account=None):
    """Return a refusal reason when the order must NOT be placed, else None.

    connected_account: account id reported by the broker session (None = unknown).
    requested_account: account named by the caller/payload (None = not named).
    """
    if live_trading_enabled():
        return None
    if requested_account is not None and str(requested_account).strip() \
            and str(requested_account).strip() != ALLOWED_ACCOUNT:
        return (
            f"account guard: requested account '{requested_account}' is not the "
            f"allowed account {ALLOWED_ACCOUNT} — order refused "
            f"(set IBKR_LIVE_TRADING_ENABLE=true in backend/.env to enable other accounts)"
        )
    if connected_account is None:
        return (
            f"account guard: broker session account is unknown; only "
            f"{ALLOWED_ACCOUNT} may receive orders — order refused"
        )
    if str(connected_account) != ALLOWED_ACCOUNT:
        return (
            f"account guard: connected account '{connected_account}' is not the "
            f"allowed account {ALLOWED_ACCOUNT} — order refused "
            f"(set IBKR_LIVE_TRADING_ENABLE=true in backend/.env to enable live trading)"
        )
    return None
