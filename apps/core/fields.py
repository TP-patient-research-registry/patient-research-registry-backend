from django.db import models
from django.utils.functional import cached_property


class EncryptableSmallIntegerField(models.PositiveSmallIntegerField):
    """
    PositiveSmallIntegerField usable inside django-cryptography's `encrypt()`.

    The stock field derives range validators from the DB column type; an encrypted column is
    binary, so that lookup crashes. Only explicitly passed validators are applied here.
    """

    @cached_property
    def validators(self):
        return [*self.default_validators, *self._validators]
