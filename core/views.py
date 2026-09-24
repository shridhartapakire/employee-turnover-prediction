import pandas as pd

from django.contrib import messages
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

    file_extension = uploaded_file.name.lower().split(".")[-1]

    if file_extension not in ["csv", "xlsx", "xls"]:
        messages.error(
            request,
            "Please upload a CSV or Excel file."
        )
        return redirect("home")

    try:

        if file_extension == "csv":
            dataframe = pd.read_csv(uploaded_file)

        elif file_extension in ["xlsx", "xls"]:
            dataframe = pd.read_excel(uploaded_file)

        else:
            raise ValueError(
                "Unsupported file type. Please upload CSV or Excel file."
            )

        if dataframe.empty:
            return render(
                request,
                "home.html",
                {"error": "The uploaded CSV or Excel file is empty."},
            )

        if "left" not in dataframe.columns:
            return render(
                request,
                "home.html",
                {"error": "Dataset must contain a 'left' column."},
            )

        if dataframe["left"].nunique() < 2:
            return render(
                request,
                "home.html",
                {"error": "The 'left' column must contain both 0 and 1 values."},
            )

        model = train_model(dataframe)

        prediction_data = dataframe.drop(columns=["left"])

        results = predict_turnover(
            model,
            prediction_data,
        )

        results["Turnover_Probability"] = (
            results["Turnover_Probability"] * 100
        ).round(2)

        employee_results = results[
            ["Predicted_Turnover", "Turnover_Probability"]
        ].to_dict("records")

        department_analysis = []

        if "Department" in dataframe.columns:
            results["Department"] = dataframe["Department"].values

            department_summary = (
                results.groupby("Department")
                .agg(
                    total_employees=("Predicted_Turnover", "count"),
                    predicted_turnover=("Predicted_Turnover", "sum"),
                    average_probability=("Turnover_Probability", "mean"),
                )
                .reset_index()
            )

            department_summary["turnover_percentage"] = (
                department_summary["predicted_turnover"]
                / department_summary["total_employees"]
                * 100
            ).round(2)

            department_summary["average_probability"] = (
                department_summary["average_probability"]
                .round(2)
            )

            department_analysis = department_summary.to_dict("records")

        turnover_count = int(
            results["Predicted_Turnover"].sum()
        )

        average_probability = round(
            results["Turnover_Probability"].mean(),
            2,
        )

        turnover_percentage = round(
            (turnover_count / len(dataframe)) * 100,
            2,
        )

        AnalysisResult.objects.create(
            user=request.user,
            upload_filename=uploaded_file.name,
            uploaded_file=uploaded_file,
            total_employees=len(dataframe),
            predicted_turnover_count=turnover_count,
            average_turnover_probability=average_probability,
        )

        return render(
            request,
            "prediction_result.html",
            {
                "filename": uploaded_file.name,
                "turnover_count": turnover_count,
                "turnover_percentage": turnover_percentage,
                "average_probability": average_probability,
                "employee_results": employee_results,
                "department_analysis": department_analysis,
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


def prediction_history(request):
    if not request.user.is_authenticated:
        return redirect("login")

    analyses = AnalysisResult.objects.filter(user=request.user)

    return render(
        request,
        "prediction_history.html",
        {"analyses": analyses},
    )

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")

    analyses = AnalysisResult.objects.filter(user=request.user)

    latest_analysis = analyses.first()

    department_summary = []

    if latest_analysis:
        try:
            dataframe = pd.read_csv(
                latest_analysis.uploaded_file.path
            )

            if "Department" in dataframe.columns:
                department_summary = (
                    dataframe["Department"]
                    .value_counts()
                    .reset_index()
                    .to_dict("records")
                )

        except Exception:
            department_summary = []

    turnover_percentage = 0

    if latest_analysis and latest_analysis.total_employees > 0:
        turnover_percentage = round(
            (
                latest_analysis.predicted_turnover_count
                / latest_analysis.total_employees
            ) * 100,
            2,
        )

    context = {
        "total_analyses": analyses.count(),
        "latest_analysis": latest_analysis,
        "turnover_percentage": turnover_percentage,
        "department_summary": department_summary,
    }

    return render(request, "dashboard.html", context)