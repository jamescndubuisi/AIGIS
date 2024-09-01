from celery import shared_task
import ast
import geopandas as gpd
import google.generativeai as genai
import numpy as np
import pandas as pd
from AIGIS import settings
from .models import Data


GOOGLE_API_KEY = settings.GOOGLE_API  # Import your function


def analyze_geojson(geojson_path, focus_column, exclude):
    # Load the GeoJSON data into a GeoDataFrame
    gdf = gpd.read_file(geojson_path)

    # Print columns for debugging
    # print("Columns in the GeoDataFrame:")
    # print(gdf.columns)
    # print(f"Key column: {focus_column}")

    # Check if the key column exists in the GeoDataFrame
    if focus_column not in gdf.columns:
        raise ValueError(f"Column '{focus_column}' not found in the GeoDataFrame.")

    # Set the key column as the index if it's not already
    if gdf.index.name != focus_column:
        gdf = gdf.set_index(focus_column)

    # Separate geometry column if it exists
    if 'geometry' in gdf.columns:
        exclude.append('geometry')
        geometry = gdf['geometry']
        gdf = gdf.drop(columns=exclude)
    else:
        geometry = None
        gdf = gdf.drop(columns=exclude)
        print("Warning: No 'geometry' column found in the GeoDataFrame.")

    # Identify numeric columns
    numeric_columns = gdf.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_columns:
        raise ValueError("No numeric columns found in the GeoDataFrame.")

    # Perform basic analysis
    analysis = {}

    # Statistics for numeric columns
    for stat in ['max', 'min', 'mean', 'sum', 'median', 'std']:
        analysis[stat] = getattr(gdf, stat)()[numeric_columns]

    # Count of all columns
    analysis['count'] = gdf.count()

    # Additional analyses
    analysis['unique_counts'] = gdf.nunique()

    # Find the key (e.g., ZipCode) with highest and lowest values for each numeric column
    for col in numeric_columns:
        max_key = gdf[col].idxmax()
        min_key = gdf[col].idxmin()
        analysis[f'{col}_highest'] = f"{focus_column}: {max_key} value: ({gdf[col].max()})"
        analysis[f'{col}_lowest'] = f"{focus_column}: {min_key} value: ({gdf[col].min()})"

    return analysis, geometry


def gemini_analyzer(data, temperature=1, top_p=0.95, top_k=64, max_output_tokens=8192,
                    response_mime_type="application/json"):
    prompt = """Analyze and Summarize the following geo data, 
                and provide a brief, interesting and rich analysis of the following data. 

                Using this JSON schema:
                Analysis = {"summary": str}
                Return a `Analysis`
                """ + str(data)

    genai.configure(api_key=GOOGLE_API_KEY)
    # Create the model
    # See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_output_tokens": max_output_tokens,
        # "response_mime_type": "text/plain",
        "response_mime_type": response_mime_type,
    }
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        safety_settings=safety_settings,
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[
        ]
    )

    response = chat_session.send_message(prompt)
    print(response)
    return response.text


def print_analysis(analysis_output, key_column):
    for stat, result in analysis_output.items():
        if isinstance(result, pd.Series):
            pass
            # print(f"{stat.capitalize()} values based on '{key_column}':")
            # print(result.to_string())
        else:
            print(f"{stat}:")
            print(result)
        # print("\n")


def analyse_file(filename, focus_column, exclude_columns, model_id):
    geojson_file_path = filename
    # key_column = 'ZipCode'
    key_column = focus_column
    exclude_columns = exclude_columns
    analysis_results = None

    try:
        analysis_results, geometry = analyze_geojson(geojson_file_path, key_column, exclude_columns)
        print("Done with analysis")
        print_analysis(analysis_results, key_column)
        print("Done printing")

        # Optional: You can use the geometry for further spatial analysis if needed
        if geometry is not None:
            print(f"Geometry column is available for spatial analysis. Shape: {geometry.shape}")
        else:
            print("No geometry column found in the GeoDataFrame.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    response = gemini_analyzer(data=analysis_results)
    response = ast.literal_eval(response)
    print(response)
    print(response["summary"])
    data_instance = Data.objects.get(id=model_id)
    data_instance.analysis = response["summary"]
    data_instance.save()

    return response["summary"]


@shared_task
def process_file(filename, focus_column, exclude_columns, model_id):
    return analyse_file(filename, focus_column, exclude_columns, model_id)
