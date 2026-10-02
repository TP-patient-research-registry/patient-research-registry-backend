from rest_framework.routers import SimpleRouter


class UUIDRouter(SimpleRouter):
    """SimpleRouter using Django path converters with `<uuid:pk>` lookups (all our PKs are UUIDs)."""

    def __init__(self, trailing_slash: bool = True):
        super().__init__(trailing_slash=trailing_slash, use_regex_path=False)
        self._default_value_pattern = "uuid"
