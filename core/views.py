import pandas as pd

from django.shortcuts import redirect, render

from .models import AnalysisResult


def home(request):
    return render(request, "home.html")


def upload_dataset(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("dataset")

        if not uploaded_file:
            return render(
                request,
                "home.html",
                {"error": "Please select a file."},
            )

        if not uploaded_file.name.lower().endswith(".csv"):
            return render(
                request,
                "home.html",
                {"error": "Please upload a CSV file."},
            )

        try:
            dataframe = pd.read_csv(uploaded_file)

            if dataframe.empty:
                return render(
                    request,
                    "home.html",
                    {"error": "The uploaded CSV is empty."},
                )

            AnalysisResult.objects.create(
                user=request.user,
                upload_filename=uploaded_file.name,
                uploaded_file=uploaded_file,
            )

            return redirect("home")

        except Exception:
            return render(
                request,
                "home.html",
                {"error": "Unable to read the CSV file."},
            )

    return redirect("home")