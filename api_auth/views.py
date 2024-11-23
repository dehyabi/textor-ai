from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .authentication import BearerTokenAuthentication
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not username or not email or not password:
            return Response({
                'error': 'Please provide username, email and password'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return Response({
                'error': 'Invalid email format'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return Response({
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return Response({
            'message': 'User registered successfully',
            'username': user.username
        }, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        print(f"Login attempt - Username: {username}")  # Debug print

        if not username or not password:
            return Response({
                'error': 'Please provide username and password'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user exists
        try:
            user_exists = User.objects.filter(username=username).exists()
            print(f"User exists in database: {user_exists}")  # Debug print
        except Exception as e:
            print(f"Error checking user existence: {str(e)}")  # Debug print
            
        user = authenticate(request, username=username, password=password)
        print(f"Authentication result: {'Success' if user else 'Failed'}")  # Debug print

        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        print(f"Token created: {created}, Token: {token.key}")  # Debug print

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username
        })

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Simply delete the token to force a login
        request.user.auth_token.delete()
        return Response({
            'message': 'Successfully logged out.'
        }, status=status.HTTP_200_OK)
