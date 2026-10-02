import pytest

from core.reconnect_policy import (
    is_feature_rejection,
    is_invalid_api_key,
    is_model_rejection,
    is_network_error,
)


@pytest.mark.parametrize(
    "message",
    [
        "INVALID_ARGUMENT: unsupported affective dialog",
        "Unknown name: proactive_audio",
        "unexpected keyword argument",
    ],
)
def test_is_feature_rejection(message):
    assert is_feature_rejection(message)


def test_is_invalid_api_key():
    assert is_invalid_api_key("API_KEY_INVALID")
    assert is_invalid_api_key("API key not valid")
    assert not is_invalid_api_key("model not found")


@pytest.mark.parametrize(
    "message",
    [
        "websocket closed with code 1007",
        "websocket closed with code 1008",
        "model not found for API version v1alpha",
    ],
)
def test_is_model_rejection(message):
    assert is_model_rejection(message)


@pytest.mark.parametrize(
    "message",
    [
        "TimeoutError",
        "request timed out",
        "getaddrinfo failed",
        "ConnectionRefusedError",
        "OSError",
        "Cannot connect to host",
    ],
)
def test_is_network_error(message):
    assert is_network_error(message)
