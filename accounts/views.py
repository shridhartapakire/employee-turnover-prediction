from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            return redirect("login")
    else:
        form = RegisterForm()

    return render(
        request,
        "register.html",
        {"form": form},
    )


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        return render(
            request,
            "login.html",
            {"error": "Invalid username or password."},
        )

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")