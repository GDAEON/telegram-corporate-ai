from prometheus_client import CollectorRegistry
from prometheus_client import Counter, Histogram

registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests received",
    ["method", "endpoint"],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Histogram of request latencies (seconds)",
    ["method", "endpoint"],
    registry=registry
)

MESSAGE_COUNT = Counter(
    "bot_messages_total",
    "Total number of processed bot messages",
    ["direction", "bot_id"],
    registry=registry,
)


MESSAGE_TEXT_COUNT = Counter(
    "bot_message_text_total",
    "Count of messages by direction, bot and text",
    ["direction", "bot_id", "text"],
    registry=registry,
)
