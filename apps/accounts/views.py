from rest_framework import generics
from rest_framework.response import Response
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
