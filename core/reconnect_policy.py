def is_feature_rejection(err_str: str) -> bool:
    lower = err_str.lower()
    return any(
        marker in lower
        for marker in (
            "invalid_argument",
            "affective",
            "proactiv",
            "unknown name",
            "unexpected keyword",
        )
    )


def is_invalid_api_key(err_str: str) -> bool:
    return "API key not valid" in err_str or "API_KEY_INVALID" in err_str


def is_model_rejection(err_str: str) -> bool:
    lower = err_str.lower()
    return any(
        marker in lower
        for marker in ("1007", "1008", "not found for api version")
    )


def is_network_error(err_str: str) -> bool:
    return any(
        marker in err_str
        for marker in (
            "TimeoutError",
            "timed out",
            "getaddrinfo",
            "CancelledError",
            "ConnectionRefusedError",
            "OSError",
            "Cannot connect",
        )
    )
