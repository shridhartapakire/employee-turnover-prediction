import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TARGET_COLUMN = "left"


def train_model(dataframe):
    """
    Train a Logistic Regression model using employee data.
    """

    if TARGET_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Dataset must contain a '{TARGET_COLUMN}' column."
        )

    data = dataframe.copy()

    X = data.drop(columns=[TARGET_COLUMN])
    y = data[TARGET_COLUMN]

    numeric_columns = X.select_dtypes(
        include=["int64", "float64"]
    ).columns

    categorical_columns = X.select_dtypes(
        include=["object", "category"]
    ).columns

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )

    model.fit(X, y)

    return model


def predict_turnover(model, dataframe):
    """
    Predict turnover probability for employees.
    """

    predictions = model.predict(dataframe)
    probabilities = model.predict_proba(dataframe)[:, 1]

    result = dataframe.copy()

    result["Predicted_Turnover"] = predictions
    result["Turnover_Probability"] = probabilities

    return result