from __future__ import annotations

import json

from . import test4


class CodeGenerationError(RuntimeError):
    pass


def generate_code() -> tuple[str, str]:
    """Invoke the Igloohome helper and return the code plus raw payload."""
    try:
        payload = test4.generate_one_time_pin()
    except (test4.IglooConfigError, test4.IglooRequestError, ValueError) as exc:
        raise CodeGenerationError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise CodeGenerationError(f"Unexpected error: {exc}") from exc

    code = payload
    if not code:
        raise CodeGenerationError("OTP code missing from response")

    #raw_output = json.dumps(payload, indent=2)
    return code
