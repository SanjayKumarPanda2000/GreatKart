from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
import datetime

class FiveMinuteTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Use email since we're doing email verification
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, '')
        return (
            str(user.pk) + user.password +
            str(email) + str(timestamp)  # timestamp is in days
        )

    def check_token(self, user, token):
        if not (user and token):
            return False

        # Parse the timestamp (days since 2001)
        try:
            ts_b36, hash = token.split("-")
            ts = int(ts_b36, 36)
        except (ValueError, AttributeError, IndexError):
            return False

        # Calculate token age in seconds
        try:
            # Days since 2001-01-01
            token_time = datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=ts)
            now = timezone.now()
            age_seconds = (now - token_time).total_seconds()
        except OverflowError:
            return False  # Invalid timestamp

        # Check if token is too old (5 minutes = 300 seconds)
        if age_seconds > 300:
            return False

        # Verify the token using parent class's method
        return super().check_token(user, token)