from apps.accounts.models import EmailVerificationToken


def create_verification_token(user):
    return EmailVerificationToken.objects.create(user=user)
