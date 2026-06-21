from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class RegisterView(APIView):

    def post(self, request):
        data = request.data

        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'customer')

        if not username or not password:
            return Response(
                {"error": "Username and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "User already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            role=role
        )

        if role == 'staff':
            user.is_approved = False
            user.save()

        return Response({
            "message": "User created successfully",
            "username": user.username,
            "role": user.role,
            "approved": user.is_approved
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):

    def post(self, request):
        data = request.data

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(
            username=username,
            password=password
        )

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.role == 'staff' and not user.is_approved:
            return Response(
                {"error": "Staff not approved by admin"},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "Login successful"
        })