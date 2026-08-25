from enum import StrEnum


class ProviderFailureCategory(StrEnum):
    AUTH_ERROR = "auth_error"
    BAD_REQUEST = "bad_request"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXHAUSTED = "quota_exhausted"
    TIMEOUT = "timeout"
    TRANSIENT_5XX = "transient_5xx"
    NETWORK_ERROR = "network_error"
    CONTENT_POLICY = "content_policy"
    UNKNOWN = "unknown"


class ProviderError(RuntimeError):
    """Safe provider error carrying classification, never a response body."""

    def __init__(
        self,
        provider_name: str,
        category: ProviderFailureCategory,
        *,
        model_name: str = "",
        status_code: int | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.category = category
        self.status_code = status_code
        status = f" status={status_code}" if status_code is not None else ""
        super().__init__(f"LLM provider {provider_name} failed: {category.value}{status}")


def status_class(status_code: int | None) -> str:
    if status_code is None:
        return "none"
    return f"{status_code // 100}xx"
