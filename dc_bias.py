"""DC bias calculations for a BJT common-emitter voltage-divider bias circuit.

This module contains engineering logic only. It must not import Flask,
know about HTTP, or render HTML.

All values are in SI units: volts (V), ohms (Ohm), amperes (A).
"""

from dataclasses import dataclass, field
import math
from typing import Mapping

VCE_SAT = 0.3  # V, collector-emitter saturation threshold

FIELD_LABELS = (
    ("vcc", "VCC"),
    ("r1", "R1"),
    ("r2", "R2"),
    ("rc", "RC"),
    ("re", "RE"),
    ("beta", "β"),
    ("vbe", "VBE"),
)

UNIT_FIELDS = ("r1", "r2", "rc", "re")


@dataclass(frozen=True)
class BiasInputs:
    """Circuit parameters in SI units."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


@dataclass(frozen=True)
class BiasResult:
    """DC operating point in SI units."""

    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str = "active"
    warnings: list[str] = field(default_factory=list)


def calculate_dc_bias(inputs: BiasInputs) -> BiasResult:
    """Calculate the DC operating point with the forward-active model.

    Assumes constant beta and constant VBE (see design doc section 7).

    Precondition: ``inputs`` passed ``validate_inputs()`` — every value is
    positive and finite, so ``r1 + r2 > 0`` and no division by zero occurs.
    """
    vth = inputs.vcc * inputs.r2 / (inputs.r1 + inputs.r2)
    rth = inputs.r1 * inputs.r2 / (inputs.r1 + inputs.r2)

    ib = (vth - inputs.vbe) / (rth + (inputs.beta + 1.0) * inputs.re)

    if ib < 0.0:
        ib = 0.0
        ic = 0.0
        ie = 0.0
        vc = inputs.vcc
    else:
        ic = inputs.beta * ib
        ie = (inputs.beta + 1.0) * ib
        vc = inputs.vcc - ic * inputs.rc

    ve = ie * inputs.re
    vb = ve + inputs.vbe
    vce = vc - ve

    region = "active"
    warnings: list[str] = []
    if vth <= inputs.vbe:
        region = "cutoff"
        # No base current flows, so the base sits at the Thevenin voltage
        # instead of VE + VBE (which only holds in forward active).
        vb = vth
        warnings.append(
            "วงจรอยู่ในช่วง Cutoff — แบบจำลอง Forward-Active ใช้ไม่ได้"
        )
    elif vce < VCE_SAT:
        region = "saturation"
        warnings.append(
            "VCE ต่ำกว่า 0.3 V — อาจอยู่ในช่วง Saturation "
            "ผลจากแบบจำลอง Forward-Active ไม่น่าเชื่อถือ"
        )

    return BiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )


def _unit_multiplier(unit: str | None) -> float:
    """Return the multiplier that converts a form value to ohms."""
    return 1.0 if unit == "ohm" else 1000.0


def validate_inputs(inputs: BiasInputs) -> list[str]:
    """Return human-readable errors for out-of-range values (empty if valid)."""
    errors: list[str] = []
    for name, label in FIELD_LABELS:
        value = getattr(inputs, name)
        if not math.isfinite(value):
            errors.append(f"{label} ต้องเป็นจำนวนจำกัด")
        elif value <= 0:
            errors.append(f"{label} ต้องเป็นค่ามากกว่าศูนย์")
    if inputs.r1 + inputs.r2 <= 0:
        errors.append("R1 + R2 ต้องมากกว่าศูนย์")
    return errors


def parse_form(form: Mapping[str, str]) -> tuple[BiasInputs | None, list[str]]:
    """Parse raw form strings into SI-unit inputs, collecting every error.

    Resistor fields are scaled by their ``*_unit`` selector (``ohm`` or
    ``kohm``; ``kohm`` is the default).
    """
    errors: list[str] = []
    values: dict[str, float] = {}

    for name, label in FIELD_LABELS:
        raw = form.get(name)
        text = "" if raw is None else str(raw).strip()
        if not text:
            errors.append(f"{label} ต้องเป็นตัวเลข")
            continue
        try:
            values[name] = float(text)
        except ValueError:
            errors.append(f"{label} ต้องเป็นตัวเลข")

    for name in UNIT_FIELDS:
        if name in values:
            values[name] *= _unit_multiplier(form.get(f"{name}_unit"))

    if errors:
        return None, errors

    inputs = BiasInputs(**values)
    range_errors = validate_inputs(inputs)
    if range_errors:
        return None, range_errors
    return inputs, []
