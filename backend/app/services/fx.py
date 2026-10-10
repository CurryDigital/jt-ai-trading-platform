"""Shared FX conversion helper — the ONLY place backend code converts currency.

Currency-audit fix (kanban t_22dee93d / t_65d96f4a, user-directed 2026-10-09).
Audit: /home/ubuntu/.hermes/profiles/qr_research/workspace/currency_audit_2026-10-09.md

Contract (binding):
- ONE shared helper; no route or component converts on its own.
- Rate source: the IBKR account payload's ExchangeRate rows
  (``$LEDGER-ExchangeRate`` per currency in ``ib.accountValues()``), or a
  stored daily rate carrying a date. Missing/undetectable rate -> raise
  ``FxRateUnavailable`` (callers surface an error, NEVER a default rate).
- Semantics verified against the live DUP825942 payload (2026-10-10):
  ``$LEDGER-ExchangeRate`` value = units of BASE currency per 1 unit of the
  row currency. BASE=HKD: HKD row = 1.00, USD row = 7.8476553.
  So ``amount_base = amount_ccy * rate[ccy]`` and ``amount_usd = amount_hkd /
  rate['USD']``.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


class FxRateUnavailable(RuntimeError):
    """Raised when a conversion is requested without a usable rate.

    Callers must surface this as an error/PENDING state — never substitute a
    hardcoded or remembered rate.
    """


@dataclass
class FxQuote:
    """A dated set of exchange rates against one base currency.

    rates: {currency: units of BASE per 1 unit of currency}; includes the
    base currency itself at 1.0. ``as_of`` is when the rates were observed
    (live payload fetch time) or the stored rate's date.
    """
    base_currency: str
    rates: Dict[str, float]
    as_of: str
    source: str

    def rate(self, currency: str) -> float:
        c = (currency or "").upper()
        if c == self.base_currency:
            return 1.0
        r = self.rates.get(c)
        if r is None or r <= 0:
            raise FxRateUnavailable(
                f"no FX rate for {c or '?'} (base {self.base_currency}) from {self.source} @ {self.as_of}"
            )
        return r

    def convert(self, amount: float, from_ccy: str, to_ccy: str) -> float:
        """Convert amount between two currencies via the base. Raises on gap."""
        frm = (from_ccy or "").upper()
        to = (to_ccy or "").upper()
        if frm == to:
            return float(amount)
        # amount -> base -> target: base = amount * rate(frm); target = base / rate(to)
        return float(amount) * self.rate(frm) / self.rate(to)

    def to_usd(self, amount: float, from_ccy: str) -> float:
        return self.convert(amount, from_ccy, "USD")

    def public_dict(self) -> dict:
        return {
            "base_currency": self.base_currency,
            "rates": dict(self.rates),
            "as_of": self.as_of,
            "source": self.source,
        }


def _detect_base_currency(rates: Dict[str, float]) -> str:
    """The base currency is the one non-BASE row whose rate is exactly 1.0
    (1 unit of itself = 1 unit of base). Verified on DUP825942: BASE=1.00,
    HKD=1.00, USD=7.8476553 -> base HKD. Zero or multiple candidates -> raise.
    """
    candidates = [c for c, r in rates.items() if c != "BASE" and abs(r - 1.0) < 1e-9]
    if len(candidates) == 1:
        return candidates[0]
    raise FxRateUnavailable(
        f"cannot detect base currency from ExchangeRate rows "
        f"(candidates with rate==1.0: {candidates or 'none'})"
    )


def quote_from_account_values(values, as_of: Optional[str] = None) -> FxQuote:
    """Build an FxQuote from ib.accountValues() rows.

    Reads the ``$LEDGER-ExchangeRate`` rows (per-currency). Raises
    FxRateUnavailable when no ExchangeRate rows are present or the base
    currency cannot be determined — callers must NOT fall back to a default.
    """
    rates: Dict[str, float] = {}
    for v in values:
        if v.tag == "$LEDGER-ExchangeRate" and v.currency:
            try:
                rates[v.currency.upper()] = float(v.value)
            except (TypeError, ValueError):
                continue
    rates.pop("BASE", None)
    if not rates:
        raise FxRateUnavailable("no $LEDGER-ExchangeRate rows in the IBKR account payload")
    base = _detect_base_currency(rates)
    return FxQuote(
        base_currency=base,
        rates=rates,
        as_of=as_of or datetime.now(timezone.utc).isoformat(),
        source="ibkr accountValues $LEDGER-ExchangeRate (live payload)",
    )
