from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Hook point for registration/email customisation (e.g. closing signups, email templates)."""
