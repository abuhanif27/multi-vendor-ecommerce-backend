
from drf_spectacular.utils import OpenApiExample

REGISTER_RESPONSE = OpenApiExample(
    "Registration Success",
    response_only=True,
    value={
        "message": "User Registration Successful. Please verify your email."
    },
)

LOGIN_RESPONSE = OpenApiExample(
    "Login Success",
    response_only=True,
    value={
        "refresh": "...",
        "access": "...",
    },
)

VERIFY_EMAIL_RESPONSE = OpenApiExample(
    "Verification Success",
    response_only=True,
    value={
        "message": "Email verified successfully."
    },
)
