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
        fields = ("email", "password1", "password2")


class UploadData(forms.ModelForm):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Enter title here'}),
        help_text='Enter a descriptive title for the data.'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter description here'}),
        help_text='Provide a detailed description of the data.'
    )
    exclude = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter exclusions here separated with commas'}),
        help_text='Specify any exclusions for the data.'
    )
    focus_column = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'What is your column of interest?'}),
        help_text='Specify the focus column for the data.'
    )
    data_file = forms.FileField(
        widget=forms.FileInput(attrs={'placeholder': 'Upload data file'}),
        help_text='Upload the data file.'
    )

    class Meta:
        model = Data
        exclude = ("user", "created", "updated", "analysis","prediction")

    def clean_data_file(self):
        data_file = self.cleaned_data.get('data_file')

        if data_file:
            # Example validation: Check file size (e.g., less than 5MB)
            if data_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 5MB.")

            # Example validation: Check file type (e.g., only allow PDF files)
            # if not data_file.name.endswith('.pdf'):
            #     raise forms.ValidationError("Only PDF files are allowed.")

            # valid_extensions = ['geojson', 'shp', 'shx', 'dbf']
            valid_extensions = ['geojson']
            file_extension = data_file.name.split('.')[-1].lower()
            print(file_extension)
            if file_extension not in valid_extensions:
                raise forms.ValidationError("The file must be a geojson file.")

        return data_file


class EditData(forms.ModelForm):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Enter title here'}),
        help_text='Enter a descriptive title for the data.'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter description here'}),
        help_text='Provide a detailed description of the data.'
    )
    # exclude = forms.CharField(
    #     max_length=100,
    #     required=False,
    #     widget=forms.TextInput(attrs={'placeholder': 'Enter exclusions here separated with commas'}),
    #     help_text='Specify any exclusions for the data.'
    # )
    # focus_column = forms.CharField(
    #     max_length=100,
    #     widget=forms.TextInput(attrs={'placeholder': 'What is your column of interest?'}),
    #     help_text='Specify the focus column for the data.'
    # )
    # data_file = forms.FileField(
    #     widget=forms.FileInput(attrs={'placeholder': 'Upload data file'}),
    #     help_text='Upload the data file.'
    # )

    class Meta:
        model = Data
        exclude = ("user", "created", "updated", "analysis","prediction","data_file", "exclude", "focus_column")

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

