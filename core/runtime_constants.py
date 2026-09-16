from zoneinfo import ZoneInfo


TZ_BR = ZoneInfo("America/Sao_Paulo")

# Static candidates used only if dynamic Live model discovery fails.
LIVE_MODEL_FALLBACKS = [
    "models/gemini-2.0-flash-live-001",
    "models/gemini-2.5-flash-native-audio-preview-09-2025",
    "models/gemini-2.0-flash-exp",
]
LIVE_MODEL = LIVE_MODEL_FALLBACKS[0]
LIVE_MODEL_CACHE_KEY = "live_model_id_cache"

CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
