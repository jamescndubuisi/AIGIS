from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from .forms import LoginForm, CreateUser, UploadData
from .models import Data
import json


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


@login_required
def upload_data(request):
    title = "Upload Data"
    context = {"title": title}
    form = UploadData(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.user = request.user
            uploaded_file.save()
            # return render(request, 'index.html')
            return redirect("home")
    context['form'] = form
    return render(request, 'upload.html', context)


class DataListView(ListView):
    queryset = Data.objects.all()
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
