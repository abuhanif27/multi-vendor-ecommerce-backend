from apps.accounts.models import EmailVerificationToken


def create_verification_token(user):
    token = EmailVerificationToken.objects.create(user=user)
    return token
