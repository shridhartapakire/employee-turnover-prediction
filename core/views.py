from django.shortcuts import redirect, render
from .models import AnalysisResult


def home(request):
    return render(request, "home.html")


def upload_dataset(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("dataset")

        if uploaded_file and uploaded_file.name.endswith(".csv"):
            AnalysisResult.objects.create(
                user=request.user,
                upload_filename=uploaded_file.name,
                uploaded_file=uploaded_file,
            )

            return redirect("home")

        return render(
            request,
            "home.html",
            {"error": "Please upload a CSV file."},
        )

    return redirect("home")