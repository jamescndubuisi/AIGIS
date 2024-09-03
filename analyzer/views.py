import ast
import json

import geopandas as gpd
import google.generativeai as genai
import numpy as np
import pandas as pd
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

from AIGIS import settings
from .forms import LoginForm, CreateUser, UploadData, EditData
from .models import Data
from .tasks import process_file

GOOGLE_API_KEY = settings.GOOGLE_API


# Create your views here.


@login_required
def homepage(request):
    title = "Home"
    message = """Hero can be anyone. Even a man knowing something as simple and reassuring as putting a coat around a young boy shoulders to let him know the world hadn’t ended.

                You fight like a younger man, there’s nothing held back. It’s admirable, but mistaken. When their enemies were at the gates the Romans would suspend democracy and appoint one man to protect the city.

            It wasn’t considered an honor, it was a public service."""
    name = request.session.get('first_name', "Anonymous")
    print(name)
    context = {"title": title, "message": message}
    return render(request, "index.html", context)


def login_page(request):
    title = "Login"
    message = ""
    purpose = "Login"
    form = LoginForm
    if request.method == "POST":
        form = form(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user=user)
                return redirect("home")
            else:
                messages.error(request, 'username or password not correct')
                return redirect('log_in')
        else:
            print("Terrible form")
            return render(
                request, "registration/login.html", {"form": form, "message": message}
            )
    return render(
        request,
        "registration/login.html",
        {"form": form, "message": message, "title": title, "purpose": purpose},
    )


def sign_up(request):
    title = "Register"
    context = {"title": title}
    form = CreateUser(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            return render(request, 'index.html')
    context['form'] = form
    return render(request, 'registration/register.html', context)


def gemini_analyzer(data, temperature=1, top_p=0.95, top_k=64, max_output_tokens=8192,
                    response_mime_type="application/json", data_description=""):
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
                Analysis = {"summary": str,"prediction":str}
                Return a `Analysis`

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
    return response.text


# def analyze_geojson(geojson_path, focus_column, exclude):
#     # Load the GeoJSON data into a GeoDataFrame
#     gdf = gpd.read_file(geojson_path)
#
#     # Print columns for debugging
#     # print("Columns in the GeoDataFrame:")
#     # print(gdf.columns)
#     # print(f"Key column: {focus_column}")
#
#     # Check if the key column exists in the GeoDataFrame
#     if focus_column not in gdf.columns:
#         raise ValueError(f"Column '{focus_column}' not found in the GeoDataFrame.")
#
#     # Set the key column as the index if it's not already
#     if gdf.index.name != focus_column:
#         gdf = gdf.set_index(focus_column)
#
#     # Separate geometry column if it exists
#     if 'geometry' in gdf.columns:
#         exclude.append('geometry')
#         geometry = gdf['geometry']
#         gdf = gdf.drop(columns=exclude)
#     else:
#         geometry = None
#         gdf = gdf.drop(columns=exclude)
#         print("Warning: No 'geometry' column found in the GeoDataFrame.")
#
#     # Identify numeric columns
#     numeric_columns = gdf.select_dtypes(include=[np.number]).columns.tolist()
#
#     if not numeric_columns:
#         raise ValueError("No numeric columns found in the GeoDataFrame.")
#
#     # Perform basic analysis
#     analysis = {}
#
#     # Statistics for numeric columns
#     for stat in ['max', 'min', 'mean', 'sum', 'median', 'std']:
#         analysis[stat] = getattr(gdf, stat)()[numeric_columns]
#
#     # Count of all columns
#     analysis['count'] = gdf.count()
#
#     # Additional analyses
#     analysis['unique_counts'] = gdf.nunique()
#
#     # Find the key (e.g., ZipCode) with highest and lowest values for each numeric column
#     for col in numeric_columns:
#         max_key = gdf[col].idxmax()
#         min_key = gdf[col].idxmin()
#         analysis[f'{col}_highest'] = f"{focus_column}: {max_key} value: ({gdf[col].max()})"
#         analysis[f'{col}_lowest'] = f"{focus_column}: {min_key} value: ({gdf[col].min()})"
#
#     return analysis, geometry
#

# def gemini_analyzer(data, temperature=1, top_p=0.95, top_k=64, max_output_tokens=8192,
#                     response_mime_type="application/json"):
#     prompt = """Analyze and Summarize the following geo data,
#                 and provide a brief, interesting and rich analysis of the following data.
#
#                 Using this JSON schema:
#                 Analysis = {"summary": str}
#                 Return a `Analysis`
#                 """ + str(data)
#
#     genai.configure(api_key=GOOGLE_API_KEY)
#     # Create the model
#     # See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
#     generation_config = {
#         "temperature": temperature,
#         "top_p": top_p,
#         "top_k": top_k,
#         "max_output_tokens": max_output_tokens,
#         # "response_mime_type": "text/plain",
#         "response_mime_type": response_mime_type,
#     }
#     safety_settings = [
#         {
#             "category": "HARM_CATEGORY_HARASSMENT",
#             "threshold": "BLOCK_MEDIUM_AND_ABOVE",
#         },
#         {
#             "category": "HARM_CATEGORY_HATE_SPEECH",
#             "threshold": "BLOCK_MEDIUM_AND_ABOVE",
#         },
#         {
#             "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
#             "threshold": "BLOCK_MEDIUM_AND_ABOVE",
#         },
#         {
#             "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
#             "threshold": "BLOCK_MEDIUM_AND_ABOVE",
#         },
#     ]
#
#     model = genai.GenerativeModel(
#         model_name="gemini-1.5-pro",
#         safety_settings=safety_settings,
#         generation_config=generation_config,
#     )
#
#     chat_session = model.start_chat(
#         history=[
#         ]
#     )
#
#     response = chat_session.send_message(prompt)
#     print(response)
#     return response.text


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


# def analyse_file(filename, focus_column, exclude_columns):
#     geojson_file_path = filename
#     # key_column = 'ZipCode'
#     key_column = focus_column
#     exclude_columns = exclude_columns
#     analysis_results = None
#
#     try:
#         analysis_results, geometry = analyze_geojson(geojson_file_path, key_column, exclude_columns)
#         print("Done with analysis")
#         print_analysis(analysis_results, key_column)
#         print("Done printing")
#
#         # Optional: You can use the geometry for further spatial analysis if needed
#         if geometry is not None:
#             print(f"Geometry column is available for spatial analysis. Shape: {geometry.shape}")
#         else:
#             print("No geometry column found in the GeoDataFrame.")
#
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
#
#     response = gemini_analyzer(data=analysis_results)
#     response = ast.literal_eval(response)
#     print(response)
#     print(response["summary"])
#
#     return response["summary"]
def analyse_file(geojson_path, key_column, exclude):

    gdf = gpd.read_file(geojson_path)

    print("Columns in the GeoDataFrame:")
    print(gdf.columns)
    print(f"Key column: {key_column}")

    if key_column not in gdf.columns:
        raise ValueError(f"Column '{key_column}' not found in the GeoDataFrame.")

    # Set the key column as the index if it's not already
    if gdf.index.name != key_column:
        gdf = gdf.set_index(key_column)

    # Separate geometry column if it exists
    # if 'geometry' in gdf.columns:
    #     geometry = gdf['geometry']
    #     gdf = gdf.drop(columns=['geometry'])
    # else:
    #     geometry = None
    #     print("Warning: No 'geometry' column found in the GeoDataFrame.")
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



    return analysis, geometry


def run_analysis_sync(geojson_file_path, key_column, exclude_columns, description):
    try:
        analysis_results, geometry = analyse_file(geojson_file_path, key_column, exclude_columns)
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

    response = gemini_analyzer(data=analysis_results, data_description=description)
    response = ast.literal_eval(response)
    # print(response)
    print(response["summary"])
    print(response["prediction"])

    return response["summary"], response["prediction"]


@login_required
def upload_data(request):
    title = "Upload Data"
    context = {"title": title}
    form = UploadData(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            exclude = form.cleaned_data['exclude']
            if exclude:
                exclusion_list = exclude.split(",")

                # Remove any leading or trailing whitespace from each word
                exclusion_list = [word.strip() for word in exclusion_list]
            else:
                exclusion_list = []
            focus_column = form.cleaned_data['focus_column']
            description = form.cleaned_data['description']
            uploaded_file = form.save(commit=False)
            uploaded_file.user = request.user

            if settings.SYNC:
                uploaded_file.analysis, uploaded_file.prediction = run_analysis_sync(request.FILES.get('data_file'),
                                                                    focus_column, exclusion_list, description)
                uploaded_file.save()
            else:
                uploaded_file.save()
                print("Before task")
                task = process_file.delay(filename=uploaded_file.data_file.path, focus_column=focus_column,
                                          exclude_columns=exclusion_list, model_id=uploaded_file.id,
                                          description=description
                                          )
                print(task.id)
                print("task started")

            return redirect("list")
    context['form'] = form
    return render(request, 'upload.html', context)


class DataListView(ListView):
    queryset = Data.objects.all().order_by('-updated')
    template_name = 'data_list.html'

    def get_context_data(self, *args, **kwargs):
        context = super(DataListView, self).get_context_data(**kwargs)
        context['title'] = "Data List"
        context['search'] = False
        return context


class DataDetailView(DetailView):
    model = Data
    template_name = 'data_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(DataDetailView, self).get_context_data(**kwargs)
        context['title'] = "Data Detail"
        context['search'] = False
        data_instance = self.get_object()
        with open(data_instance.data_file.path, 'r') as file:
            geojson_data = json.load(file)

        context['geojson_data'] = json.dumps(geojson_data)
        return context


class DataUpdateView(UpdateView):
    model = Data
    template_name = 'upload.html'
    form_class = EditData

    def get_context_data(self, *args, **kwargs):
        context = super(DataUpdateView, self).get_context_data(**kwargs)
        context['title'] = "Data Update"
        context['search'] = False
        return context


class DataDeleteView(DeleteView):
    model = Data
    template_name = 'delete_data.html'
    success_url = reverse_lazy('list')  # Redirect to data list after deletion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete Data"
        context['search'] = False
        return context


