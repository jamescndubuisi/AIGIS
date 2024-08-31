import geopandas as gpd
import pandas as pd
import numpy as np
import google.generativeai as genai

from AIGIS import settings

GOOGLE_API_KEY = settings.GOOGLE_API


def analyze_geojson(geojson_path, focus_column, exclude_columns):
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
        exclude_columns.append('geometry')
        geometry = gdf['geometry']
        gdf = gdf.drop(columns=exclude_columns)
    else:
        geometry = None
        gdf = gdf.drop(columns=exclude_columns)
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


def print_analysis(analysis_results, key_column):
    for stat, result in analysis_results.items():
        if isinstance(result, pd.Series):
            pass
            # print(f"{stat.capitalize()} values based on '{key_column}':")
            # print(result.to_string())
        else:
            print(f"{stat}:")
            print(result)
        # print("\n")


geojson_file_path = "data.geojson"
key_column = 'ZipCode'
exclude_columns = ['OBJECTID']

try:
    analysis_results, geometry = analyze_geojson(geojson_file_path, key_column, exclude_columns)
    print_analysis(analysis_results, key_column)

    # Optional: You can use the geometry for further spatial analysis if needed
    if geometry is not None:
        print(f"Geometry column is available for spatial analysis. Shape: {geometry.shape}")
    else:
        print("No geometry column found in the GeoDataFrame.")

except Exception as e:
    print(f"An error occurred: {str(e)}")


def gemini_news_summarizer(data="", temperature=1, top_p=0.95, top_k=64, max_output_tokens=8192,
                           response_mime_type="application/json", category="political"):
    prompt = "Analyze and Summarize the following geo data, and provide a detailed analysis of the data. " \

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

    response = chat_session.send_message(prompt + data)

    # punny_article = PunnyArticle.objects.create(
    #     title=article.title,
    #     content=response.text,
    #     category=article.category,
    #     date_published=article.date_published,
    #     source_article=article
    # )
    #
    # punny_article.save()

    # print(response.text)
    return response.text
