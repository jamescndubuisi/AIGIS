from celery import shared_task
import ast
import geopandas as gpd
import google.generativeai as genai
import numpy as np
import pandas as pd
from .models import Data
from libpysal.weights import Queen
from esda.moran import Moran
from AIGIS import settings

GOOGLE_API_KEY = settings.GOOGLE_API  # Import your function


def analyze_geojson1(geojson_path, focus_column, exclude):
    print("task started 4")
    # Load the GeoJSON data into a GeoDataFrame
    gdf = gpd.read_file(geojson_path)

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
        analysis[f'{col}_highest'] = f"{focus_column}: {max_key} value: {gdf[col].max()}"
        analysis[f'{col}_lowest'] = f"{focus_column}: {min_key} value: {gdf[col].min()}"

    return analysis, geometry


def analyze_geojson(geojson_path, key_column, exclude):
    # Load the GeoJSON data into a GeoDataFrame
    gdf = gpd.read_file(geojson_path)

    print("Columns in the GeoDataFrame:")
    print(gdf.columns)
    print(f"Key column: {key_column}")

    if key_column not in gdf.columns:
        raise ValueError(f"Column '{key_column}' not found in the GeoDataFrame.")

    # Set the key column as the index if it's not already
    if gdf.index.name != key_column:
        gdf = gdf.set_index(key_column)


    if 'geometry' in gdf.columns:
        exclude.append('geometry')
        geometry = gdf['geometry']
        if exclude:
            gdf = gdf.drop(columns=exclude)
    else:
        geometry = None
        if exclude:
            gdf = gdf.drop(columns=exclude)
        print("Warning: No 'geometry' column found in the GeoDataFrame.")

    # Identify numeric columns
    numeric_columns = []
    for col in gdf.columns:
        try:
            pd.to_numeric(gdf[col])  # Attempt to convert to numeric
            numeric_columns.append(col)
        except ValueError:
            pass  # Ignore col
        except TypeError:
            pass
        except:
            pass

    print(numeric_columns)

    for col in numeric_columns:
        gdf[col] = pd.to_numeric(gdf[col], errors='coerce')
        # Replace both NaN (from conversion) and existing None with 0
        gdf[col] = gdf[col].fillna(0)

    if not numeric_columns:
        raise ValueError("No numeric columns found in the GeoDataFrame.")

    # Perform basic analysis
    analysis = {}

    # Statistics for numeric columns
    for stat in ['max', 'min', 'mean', 'sum', 'median', 'std']:
        analysis[stat] = getattr(gdf[numeric_columns], stat)()

    # Count of all columns
    analysis['count'] = gdf.count()

    # Additional analyses
    analysis['unique_counts'] = gdf.nunique()

    # Find the key with highest and lowest values for each numeric column
    for col in numeric_columns:
        max_key = gdf[col].idxmax()
        min_key = gdf[col].idxmin()
        analysis[f'{col}_highest'] = f"{key_column}: {max_key} value: ({gdf[col].max()})"
        analysis[f'{col}_lowest'] = f"{key_column}: {min_key} value: ({gdf[col].min()})"

    # Correlation Matrix for Numeric Columns
    correlation_matrix = gdf[numeric_columns].corr()
    analysis['correlation_matrix'] = correlation_matrix.to_dict()

    # Distribution Analysis (Skewness and Kurtosis)
    analysis['skewness'] = gdf[numeric_columns].skew().to_dict()
    analysis['kurtosis'] = gdf[numeric_columns].kurtosis().to_dict()

    # # Outlier Detection (using IQR)
    # for col in numeric_columns:
    #     Q1 = gdf[col].quantile(0.25)
    #     Q3 = gdf[col].quantile(0.75)
    #     IQR = Q3 - Q1
    #     lower_bound = Q1 - 1.5 * IQR
    #     upper_bound = Q3 + 1.5 * IQR
    #     outliers = gdf[(gdf[col] < lower_bound) | (gdf[col] > upper_bound)].index.tolist()
    #     analysis[f'{col}_outliers'] = outliers
    #
    # if geometry is not None:
    #     # Spatial autocorrelation using Moran's I
    #     gdf_with_geometry = gpd.GeoDataFrame(gdf, geometry=geometry)
    #     w = Queen.from_dataframe(gdf_with_geometry)
    #     for col in numeric_columns:
    #         mi = Moran(gdf[col], w)
    #         analysis[f'{col}_morans_i'] = mi.I

    return analysis, geometry


def gemini_analyzer(data, temperature=1, top_p=0.95, top_k=64, max_output_tokens=8192,
                    response_mime_type="application/json", data_description=""):
    print("task started : gemini analyzer function")
    prompt = """
                    Instruction:
                    Generate insightful analysis and summary, and make predictions the following geo data. 
                    Provide an interesting and rich analysis of the following data. 
                    Also make logical predictions and explain your reasoning
                    important: ignore statistics that don't make sense, like maximum mean median and mode of columns like phone 
                    number, house address number and the likes ignore phone number statistics in predictions and summary, 
                    use more meaningful statistics.
                    try figuring out what abbreviations mean and figure out other relevant information like
                    like postcode and zip codes based on geological knowledge.
                    Ignore mentioning data you do not consider useful.  

                    Avoid stating very obvious facts 


                    Using this JSON schema:
                    ensure to follow this output format 
                    {"summary": str,"prediction":str}
                    Return {"summary": str,"prediction":str}
                    

                """ + str(data) + f"""Data Description: {data_description} """

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
        model_name="gemini-1.5-pro-exp-0827",
        safety_settings=safety_settings,
        generation_config=generation_config,
    )

    chat_session = model.start_chat(
        history=[
        ]
    )

    response = chat_session.send_message(prompt)
    print(response)
    print("task done : gemini analyzer function")
    return response.text


def print_analysis(analysis_output, key_column):
    print("task started : print analysis function")
    for stat, result in analysis_output.items():
        if isinstance(result, pd.Series):
            pass
            # print(f"{stat.capitalize()} values based on '{key_column}':")
            # print(result.to_string())
        else:
            print(f"{stat}:")
            print(result)
    print("task done : print analysis function")
        # print("\n")


def analyse_file(filename, focus_column, exclude_columns, model_id, description):
    print("task started : analyse file function")
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
        status = "Completed"

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        status = "Failed"

    try:
        response = gemini_analyzer(data=analysis_results, data_description=description)
        response = ast.literal_eval(response)
        status = "Completed"
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        response = None
        status = "Failed"
    print(response)
    # print(response["summary"])




    print(response["prediction"])
    data_instance = Data.objects.get(id=model_id)
    data_instance.analysis = response["summary"]
    data_instance.prediction = response["prediction"]
    data_instance.analysis_status = status
    data_instance.save()
    print("task done : analyse file function")
    return response["summary"]


@shared_task
def process_file(filename, focus_column, exclude_columns, model_id, description):
    print("task started : process file function")
    return analyse_file(filename, focus_column, exclude_columns, model_id, description)
