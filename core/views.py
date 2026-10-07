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
        messages.error(request, "Please upload a CSV or Excel file.")
        return redirect("home")

    try:
        if file_extension == "csv":
            dataframe = pd.read_csv(uploaded_file)

        elif file_extension in ["xlsx", "xls"]:
            dataframe = pd.read_excel(uploaded_file)

        else:
            raise ValueError("Unsupported file type. Please upload CSV or Excel file.")

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
                {"error": ("The 'left' column must contain both 0 and 1 values.")},
            )

        model = train_model(dataframe)

        prediction_data = dataframe.drop(columns=["left"])

        results = predict_turnover(
            model,
            prediction_data,
        )

        results["Turnover_Probability"] = (results["Turnover_Probability"] * 100).round(
            2
        )

        # Estimated turnover cost
        TURNOVER_COST_MULTIPLIER = 1.5

        results["Estimated_Turnover_Cost"] = 0.0

        if "MonthlyIncome" in results.columns:
            results["Estimated_Turnover_Cost"] = (
                results["MonthlyIncome"].astype(float) * 12 * TURNOVER_COST_MULTIPLIER
            )

            results.loc[
                results["Predicted_Turnover"] == 0, "Estimated_Turnover_Cost"
            ] = 0.0

        total_turnover_cost = round(
            results["Estimated_Turnover_Cost"].sum(),
            2,
        )

        results["Retention_Priority"] = (
            results["Turnover_Probability"]
            * 0.01
            * results["Estimated_Turnover_Cost"]
        ).round(2)

        # Employee retention risk level
        results["Risk_Level"] = results["Turnover_Probability"].apply(
            lambda probability: (
                "High Risk"
                if probability >= 70
                else "Medium Risk" if probability >= 40 else "Low Risk"
            )
        )

                # Workforce efficiency proxy
        efficiency_columns = [
            "JobInvolvement",
            "PerformanceRating",
            "JobLevel",
            "YearsAtCompany",
        ]

        available_efficiency_columns = [
            column
            for column in efficiency_columns
            if column in results.columns
        ]

        if available_efficiency_columns:
            efficiency_data = results[available_efficiency_columns].copy()

            for column in available_efficiency_columns:
                minimum = efficiency_data[column].min()
                maximum = efficiency_data[column].max()

                if maximum != minimum:
                    efficiency_data[column] = (
                        (efficiency_data[column] - minimum)
                        / (maximum - minimum)
                    ) * 100
                else:
                    efficiency_data[column] = 50

            results["Efficiency_Score"] = (
                efficiency_data.mean(axis=1)
            ).round(2)

        else:
            results["Efficiency_Score"] = 0.0

        employee_results = results[
            [
                "Predicted_Turnover",
                "Turnover_Probability",
                "Risk_Level",
                "Estimated_Turnover_Cost",
                "Retention_Priority",
                "Efficiency_Score",
            ]
        ].to_dict("records")

        # Department analysis
        department_analysis = []

        if "Department" in dataframe.columns:
            results["Department"] = dataframe["Department"].values

            department_summary = (
                results.groupby("Department")
                .agg(
                    total_employees=("Predicted_Turnover", "count"),
                    predicted_turnover=("Predicted_Turnover", "sum"),
                    average_probability=("Turnover_Probability", "mean"),
                    estimated_turnover_cost=(
                        "Estimated_Turnover_Cost",
                        "sum",
                    ),
                )
                .reset_index()
            )

            department_summary["turnover_percentage"] = (
                department_summary["predicted_turnover"]
                / department_summary["total_employees"]
                * 100
            ).round(2)

            department_summary["average_probability"] = department_summary[
                "average_probability"
            ].round(2)

            department_summary["estimated_turnover_cost"] = department_summary[
                "estimated_turnover_cost"
            ].round(2)

            department_analysis = department_summary.to_dict("records")

        # Job role analysis
        job_role_analysis = []

        if "JobRole" in dataframe.columns:
            results["JobRole"] = dataframe["JobRole"].values

            job_role_summary = (
                results.groupby("JobRole")
                .agg(
                    total_employees=("Predicted_Turnover", "count"),
                    predicted_turnover=("Predicted_Turnover", "sum"),
                    average_probability=("Turnover_Probability", "mean"),
                )
                .reset_index()
            )

            job_role_summary["turnover_percentage"] = (
                job_role_summary["predicted_turnover"]
                / job_role_summary["total_employees"]
                * 100
            ).round(2)

            job_role_summary["average_probability"] = job_role_summary[
                "average_probability"
            ].round(2)

            job_role_analysis = job_role_summary.to_dict("records")

        turnover_count = int(results["Predicted_Turnover"].sum())

        average_probability = round(
            results["Turnover_Probability"].mean(),
            2,
        )

        average_efficiency = round(
            results["Efficiency_Score"].mean(),
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
                "total_turnover_cost": total_turnover_cost,
                "employee_results": employee_results,
                "department_analysis": department_analysis,
                "department_chart_labels": [
                    department["Department"]
                    for department in department_analysis
                ],
                "department_chart_values": [
                    department["predicted_turnover"]
                    for department in department_analysis
                ],
                "job_role_analysis": job_role_analysis,
                "average_efficiency": average_efficiency,
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
    job_role_summary = []
    turnover_percentage = 0

    if latest_analysis:
        try:
            file_extension = latest_analysis.upload_filename.lower().split(".")[-1]

            if file_extension == "csv":
                dataframe = pd.read_csv(latest_analysis.uploaded_file.path)

            elif file_extension in ["xlsx", "xls"]:
                dataframe = pd.read_excel(latest_analysis.uploaded_file.path)

            else:
                dataframe = None

            if dataframe is not None:
                if "Department" in dataframe.columns:
                    department_summary = (
                        dataframe["Department"]
                        .value_counts()
                        .reset_index()
                        .to_dict("records")
                    )

                if "JobRole" in dataframe.columns:
                    job_role_summary = (
                        dataframe["JobRole"]
                        .value_counts()
                        .reset_index()
                        .to_dict("records")
                    )

        except Exception:
            department_summary = []
            job_role_summary = []

    if latest_analysis and latest_analysis.total_employees > 0:
        turnover_percentage = round(
            (latest_analysis.predicted_turnover_count / latest_analysis.total_employees)
            * 100,
            2,
        )

    context = {
        "total_analyses": analyses.count(),
        "latest_analysis": latest_analysis,
        "turnover_percentage": turnover_percentage,
        "department_summary": department_summary,
        "job_role_summary": job_role_summary,
    }

    return render(request, "dashboard.html", context)
