from django.db import models
from django.utils.translation import gettext_lazy as _  # Django 4.0
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.urls import reverse

# Create your models here.


class UserManager(BaseUserManager):
    use_in_migrations = False

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        print("create user")
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_staff", False)
        return self._create_user(email, password, **extra_fields)

    def create_staff_user(self, email, password=None):
        user = self.create_user(email=email, password=password, is_staff=True)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


# Create your models here.
class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True, null=True)
    username = None
    created = models.DateField(auto_now=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Data(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_file = models.FileField(upload_to="data_files/")

    class Meta:
        verbose_name = _("Data")
        verbose_name_plural = _("Data")

    def get_absolute_url(self):
        return reverse("detail", kwargs={"pk": self.pk})

    def __str__(self):
        return self.title

    # def clean(self):
    #     super().clean()  # Call the parent class's clean method
    #
    #     # Example validation: Check if the file is not empty
    #     if not self.data_file:
    #         raise ValidationError("The file cannot be empty.")
    #
    #     # Example validation: Check if the file size is within a certain limit (e.g., 5MB)
    #     max_size = 5 * 1024 * 1024  # 5MB in bytes
    #     if self.data_file.size > max_size:
    #         raise ValidationError("The file size must be less than 5MB.")
    #
    #     # Example validation: Check if the file has a valid extension
    #     valid_extensions = ['.pdf', '.docx', '.txt']
    #     file_extension = self.data_file.name.split('.')[-1].lower()
    #     if file_extension not in valid_extensions:
    #         raise ValidationError("The file must be a PDF, DOCX, or TXT file.")
    #
    # def save(self, *args, **kwargs):
    #     self.clean()  # Call the clean method before saving
    #     super().save(*args, **kwargs)
