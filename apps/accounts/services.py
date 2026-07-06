from apps.accounts.models import EmailVerificationToken


def create_verification_token(user):
    return EmailVerificationToken.objects.create(user=user)


def build_email_verification_link(token):
    return f"http://127.0.0.1:8000/api/v1/auth/verify-email/?token={token.token}"


def send_verification_email(user):
    token = create_verification_token(user)
    link = build_email_verification_link(token)
    print(link)
