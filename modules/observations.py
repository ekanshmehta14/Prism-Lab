import pandas as pd

SIDES = {"Left", "Right"}
ORDERS = {1, 2}


def validate_observation(row):
    if row.get("side") not in SIDES:
        raise ValueError("Side must be Left or Right.")
    order = int(row.get("order", 0))
    if order not in ORDERS:
        raise ValueError("Only first and second spectral orders are allowed.")
    if not row.get("spectral_colour") and not row.get("spectral_line"):
        raise ValueError("A spectral colour or line is required.")
    return True


def add_observation(state, observation):
    validate_observation(observation)
    observation["id"] = len(state["observations"])+1
    state["observations"] = [*state["observations"], observation.copy()]


def observations_frame(state):
    if not state["observations"]:
        return pd.DataFrame(columns=["id","side","order","spectral_colour","spectral_line","wavelength_nm","main_scale","vernier","least_count","final_reading","minimum_deviation","source","verified"])
    return pd.DataFrame(state["observations"])


def validate_import_payload(payload):
    if not isinstance(payload, dict) or "observations" not in payload:
        raise ValueError("Invalid experiment JSON: observations list is missing.")
    result = []
    for row in payload["observations"]:
        validate_observation(row)
        result.append(row)
    return payload
