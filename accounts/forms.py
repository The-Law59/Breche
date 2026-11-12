from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Team, User


class SignupForm(UserCreationForm):
    email = forms.EmailField(label="Adresse e-mail", required=True)

    class Meta:
        model = User
        fields = ("username", "email", "school")
        labels = {"username": "Pseudo", "school": "Établissement (facultatif)"}
        help_texts = {"username": "Visible dans le classement. Lettres, chiffres et @ . + - _ uniquement."}

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte utilise déjà cette adresse.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "school", "bio")
        labels = {"email": "Adresse e-mail"}
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name", "description")
        labels = {"name": "Nom de l'équipe", "description": "Description (facultatif)"}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if Team.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("Ce nom est déjà pris.")
        return name


class TeamJoinForm(forms.Form):
    code = forms.CharField(label="Code d'invitation", max_length=16)
