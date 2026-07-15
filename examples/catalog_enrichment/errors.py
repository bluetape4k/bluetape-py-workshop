from typing import Literal

RequiredFailureCode = Literal["provider_unavailable", "response_invalid"]


class InvalidProductIdentifier(ValueError):  # noqa: N818 - domain name
    def __init__(self, index: int, reason: str) -> None:
        self.index = index
        self.reason = reason
        super().__init__(f"product_ids[{index}]: {reason}")


class TooManyProductIdentifiers(ValueError):  # noqa: N818 - domain name
    def __init__(self, limit: int) -> None:
        self.limit = limit
        super().__init__(f"product_ids must contain at most {limit} values")


class ProviderUnavailable(RuntimeError):  # noqa: N818 - provider signal
    def __init__(self) -> None:
        super().__init__("provider unavailable")


class RequiredProviderFailure(RuntimeError):  # noqa: N818 - domain name
    def __init__(self, batch_index: int, code: RequiredFailureCode) -> None:
        self.batch_index = batch_index
        self.code = code
        super().__init__(f"required provider failed for batch {batch_index}: {code}")


class CatalogEnrichmentFailed(RuntimeError):  # noqa: N818 - domain name
    def __init__(self, failures: tuple[RequiredProviderFailure, ...]) -> None:
        self.failures = failures
        batches = ", ".join(str(failure.batch_index) for failure in failures)
        super().__init__(f"catalog enrichment failed for required batch {batches}")
