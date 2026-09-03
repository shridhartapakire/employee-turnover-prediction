import pandas as pd

from django.shortcuts import redirect, render

from .models import AnalysisResult
from ml.predictor import train_model, predict_turnover


def home(request):
    return render(request, "home.html")


def upload_dataset(request):
    if request.method != "POST":
        return redirect("home")

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

        model = train_model(dataframe)

        prediction_data = dataframe.drop(columns=["left"])

        results = predict_turnover(
            model,
            prediction_data,
        )

        turnover_count = int(
            results["Predicted_Turnover"].sum()
        )

        average_probability = round(
            results["Turnover_Probability"].mean() * 100,
            2,
        )

        AnalysisResult.objects.create(
            user=request.user,
            upload_filename=uploaded_file.name,
            uploaded_file=uploaded_file,
        )

        return render(
            request,
            "prediction_result.html",
            {
                "filename": uploaded_file.name,
                "turnover_count": turnover_count,
                "average_probability": average_probability,
            },
        )

    except ValueError as error:
        return render(
            request,
            "home.html",
            {"error": str(error)},
        )

    except Exception:
        return render(
            request,
            "home.html",
            {"error": "Unable to process the dataset."},
        )