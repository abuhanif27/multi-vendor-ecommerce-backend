from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.accounts.serializers import RegisterSerializer
from apps.accounts.models import EmailVerificationToken


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = EmailVerificationToken.objects.create(user=user)

        print("=" * 80)
        print("EMAIL VERIFICATION LINK")
        print(
            f"http://127.0.0.1:8000/api/v1/auth/verify-email/?token={token.token}")
        print("=" * 80)

        return Response(
            {

                "message": "User Registration Successful. Please verify your email.",
            }
        )


class VerifyEmailAPIView(APIView):

    def get(self, request):
        token = request.query_params.get("token")

        verification = get_object_or_404(
            EmailVerificationToken,
            token=token,
        )

        if verification.is_expired:
            return Response(
                {
                    "message": "Verification link has expired."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = verification.user
        user.is_verified = True
        user.save(update_fields=["is_verified"])

        verification.delete()

        return Response(
            {
                "message": "Email verified successfully."
            }
        )
