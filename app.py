"""Flask application for the BJT DC bias calculator.

HTTP layer only: parsing form data, calling the engineering module and
rendering the template. All circuit math lives in ``dc_bias.py``.
"""

from flask import Flask, render_template, request

from dc_bias import calculate_dc_bias, parse_form

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12",
    "r1": "100", "r1_unit": "kohm",
    "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm",
    "re": "1", "re_unit": "kohm",
    "beta": "100",
    "vbe": "0.70",
}

RESISTORS = (
    ("r1", "R1", "ต่อ VCC–Base"),
    ("r2", "R2", "ต่อ Base–Ground"),
    ("rc", "RC", "ต่อ VCC–Collector"),
    ("re", "RE", "ต่อ Emitter–Ground"),
)


@app.template_filter("fmt")
def fmt(value: float, digits: int = 3) -> str:
    """Format a number with a fixed number of decimals."""
    return f"{value:.{digits}f}"


@app.get("/")
def index():
    return render_template(
        "index.html",
        form=DEFAULTS,
        result=None,
        errors=[],
        warnings=[],
        resistors=RESISTORS,
    )


@app.post("/calculate")
def calculate():
    inputs, errors = parse_form(request.form)
    if errors:
        return (
            render_template(
                "index.html",
                form=request.form,
                result=None,
                errors=errors,
                warnings=[],
                resistors=RESISTORS,
            ),
            400,
        )

    result = calculate_dc_bias(inputs)
    return render_template(
        "index.html",
        form=request.form,
        result=result,
        errors=[],
        warnings=result.warnings,
        resistors=RESISTORS,
    )


if __name__ == "__main__":
    app.run(debug=True)
