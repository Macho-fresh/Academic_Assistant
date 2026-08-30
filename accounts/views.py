from django.shortcuts import render
from rest_framework.views import APIView
from .models import *
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
# from .forms import RegisterForm
from rest_framework.permissions import IsAuthenticated

class LoginView(APIView):

    def get(self, request):
        return render(request, "accounts/login.html")

    def post(self, request):
        print('logging in..')
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "accounts/login.html")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is None:
            messages.error(request, "Invalid email or password.")
            return render(request, "accounts/login.html")

        login(request, user)
        print("LOGGED IN USER:", request.user)
        print("AUTHENTICATED:", request.user.is_authenticated)  

        return redirect("dashboard")

class RegisterView(APIView):

    def get(self, request):
        return render(request, "accounts/register.html")

    def post(self, request):
        print("REGISTER POST HIT")
        print(request.data)

        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        email = request.data.get("email")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")
        role = request.data.get("role")
        department = request.data.get("department")

        if password != confirm_password:
            return render(
                request,
                "accounts/register.html",
                {"error": "Passwords do not match"}
            )

        if not all([
            first_name,
            last_name,
            email,
            role,
            password,
            confirm_password
        ]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, "accounts/register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "accounts/register.html")

        if role not in ["student", "lecturer"]:
            messages.error(request, "Invalid account role.")
            return render(request, "accounts/register.html")

        User.objects.create_user(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            role=role,
            department=department
        )

        return redirect("login")

class LogoutView(APIView):

    def post(self, request):
        logout(request)

        return redirect("login")

def profile_view(request):
    return render(request, "accounts/profile.html")

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(sellf, request):
        return render(request, "dashboard/dashboard.html")    
