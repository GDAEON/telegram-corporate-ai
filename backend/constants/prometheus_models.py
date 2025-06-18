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

# Track each user and bot message by text. This can result in high
# cardinality if there are many different texts, but provides visibility
# into message contents for debugging. The text label is truncated to
# 100 characters to keep label sizes manageable.
MESSAGE_TEXT_COUNT = Counter(
    "bot_message_text_total",
    "Count of messages by direction, bot and text",
    ["direction", "bot_id", "text"],
    registry=registry,
)
