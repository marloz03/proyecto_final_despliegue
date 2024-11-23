import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import OneHotEncoder
import os


def load_data(file_path):
    """Load the CSV data into a DataFrame."""
    return pd.read_csv(file_path)


def preprocess_data(df, encoder_path, target_encoder):
    """Preprocess the data for prediction."""
    # Convert datetime columns
    df['trans_date_trans_time'] = pd.to_datetime(df['trans_date_trans_time'])
    df['dob'] = pd.to_datetime(df['dob'], format='%d/%m/%Y')

    # Calculate derived columns
    df['distancia_euclidiana'] = np.sqrt(
        (df['lat'] - df['merch_lat'])**2 + (df['long'] - df['merch_long'])**2
    )
    df['hora_decimal'] = (
        df['trans_date_trans_time'].dt.hour +
        df['trans_date_trans_time'].dt.minute / 60 +
        df['trans_date_trans_time'].dt.second / 3600
    )
    df['edad_decimal'] = (
        (df['trans_date_trans_time'] - df['dob']).dt.total_seconds() /
        (365.25 * 24 * 3600)
    )

    # Load the OneHotEncoder and transform the 'category' column
    encoder = joblib.load(encoder_path)
    encoded_categories = encoder.transform(df[['category']])
    df_encoded = pd.DataFrame(encoded_categories, columns=encoder.get_feature_names_out())

    # Concatenate the encoded columns with the original DataFrame
    df = pd.concat([df, df_encoded], axis=1)

    # Select relevant columns for the model
    selected_columns = ['distancia_euclidiana', 'hora_decimal', 'edad_decimal', 'amt', 'city_pop', 'state']
    category_columns = df.filter(regex='^category_').columns
    df_selected = df[selected_columns + list(category_columns)]

    category_target_mean = joblib.load(target_encoder)
    df_selected['state'] = df_selected['state'].map(category_target_mean)

    return df_selected


def load_model(model_path):
    """Load the trained model."""
    return joblib.load(model_path)


def make_predictions(df, model):
    """Generate predictions using the trained model."""
    return model.predict(df), model.predict_proba(df)


def save_predictions(original_df, predictions, probabilities, output_path):
    """Save predictions and probabilities to a CSV file along with the original data."""
    original_df['Prediction'] = predictions
    original_df['Probability_Fraud'] = probabilities[:, 1]
    original_df['Class'] = np.where(
        original_df['Probability_Fraud'] < 0.02, 'Muy poco probable',
        np.where(
            original_df['Probability_Fraud'] < 0.1, 'Poco probable',
            np.where(
                original_df['Probability_Fraud'] < 0.5, 'Moderadamente probable',
                'Altamente probable'
            )
        )
    )

    original_df.to_csv(output_path, index=False)



def main():
    # File paths
    input_file = "datos/fraud test.csv"
    encoder_path = "models/onehot_encoder.joblib"
    target_encoder = 'models/category_target_mean.joblib'
    model_path = "models/xgb_v2.joblib"
    output_file = "predictions/predictions.csv"

    # Load and preprocess data
    df = load_data(input_file)
    df_selected = preprocess_data(df, encoder_path, target_encoder)

    # Load the model
    model = load_model(model_path)

    # Make predictions
    predictions, probabilities = make_predictions(df_selected, model)

    # Save predictions to a file
    save_predictions(df, predictions, probabilities, output_file)


if __name__ == "__main__":
    main()









