from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.accounts.serializers import RegisterSerializer, LoginSerializer
from apps.accounts.models import EmailVerificationToken
from apps.accounts.services import send_verification_email


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            send_verification_email(user)

        return Response(
            {

                "message": "User Registration Successful. Please verify your email.",
            }, status=status.HTTP_201_CREATED
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
            }, status=status.HTTP_200_OK
        )


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )
