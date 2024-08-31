from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User , Data
from django.contrib.auth import login, authenticate


class LoginForm(forms.Form):
    email = forms.CharField(widget= forms.EmailInput(attrs={"class": "form-control", "id":"username"}))
    password = forms.CharField(widget= forms.PasswordInput(attrs={"class": "form-control",  "id":"password"}))


class CreateUser(UserCreationForm):
    email = forms.CharField(label="Email ", widget= forms.EmailInput(attrs={"class": "form-control", "id":"username"}))
    password1 = forms.CharField(label="Password ", widget=forms.PasswordInput(attrs={"class": "form-control", "id": "password"}))
    password2 = forms.CharField(label="Confirm Password ",widget=forms.PasswordInput(attrs={"class": "form-control", "id": "password"}))

    class Meta:
        model = User
        fields = ("email","password1","password2")


class UploadData(forms.ModelForm):
    # file = forms.FileField(widget=forms.FileInput(attrs={"class": "form-control", "id": "file"}))

    class Meta:
        model = Data
        exclude = ("user", "created", "updated")

    def clean_data_file(self):
        data_file = self.cleaned_data.get('data_file')

        if data_file:
            # Example validation: Check file size (e.g., less than 5MB)
            if data_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")

            # Example validation: Check file type (e.g., only allow PDF files)
            # if not data_file.name.endswith('.pdf'):
            #     raise forms.ValidationError("Only PDF files are allowed.")

            valid_extensions = ['geojson', 'shp', 'shx', 'dbf']
            file_extension = data_file.name.split('.')[-1].lower()
            print(file_extension)
            if file_extension not in valid_extensions:
                raise forms.ValidationError("The file must be geojson or shapefiles.")

        return data_file

