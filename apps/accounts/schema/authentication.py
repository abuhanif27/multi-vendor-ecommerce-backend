from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)
from apps.accounts.serializers import RegisterSerializer, LoginSerializer
from apps.accounts.schema.auth_examples import (
    REGISTER_RESPONSE,
    LOGIN_RESPONSE,
    VERIFY_EMAIL_RESPONSE,
)

REGISTER_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Register user",
        description="""
Register a new customer account.

A verification email is sent after successful registration.
""",
        request=RegisterSerializer,
        responses={
            201: None,
            400: None,
        },
        examples=[
            REGISTER_RESPONSE,
        ],
    )
)

LOGIN_SCHEMA = extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Login user",
        description="""
Login to an existing customer account.
""",
        request=LoginSerializer,
        responses={
            200: None,
            400: None,
        },
        examples=[
            LOGIN_RESPONSE,
        ],
    )
)

VERIFY_EMAIL_SCHEMA = extend_schema_view(
    get=extend_schema(
        tags=["Authentication"],
        summary="Verify email",
        description="""
Verify a user's email address using the verification token.
""",
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Email verification token.",
            )
        ],
        responses={
            200: None,
            400: None,
            404: None,
        },
        examples=[
            VERIFY_EMAIL_RESPONSE,
        ],
    )
)
