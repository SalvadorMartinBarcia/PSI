from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput
from django.contrib.auth.models import User

from datamodel.models import Game, Move
from datamodel import constants


class LogInForm(AuthenticationForm):
    username = forms.CharField(widget=TextInput(attrs={'class': ' form-style content__info text-center', 'placeholder': 'Usuario'}), label="")
    password = forms.CharField(widget=PasswordInput(attrs={'class': 'form-style content__info text-center', 'placeholder': 'Contraseña'}), label="")

    def is_valid(self):
        if not User.objects.filter(username=self.data['username']).exists():
            self.add_error(None, constants.MSG_ERROR_INVALID_LOGIN)
            return False

        if not authenticate(username=self.data['username'], password=self.data['password']):
            self.add_error(None, constants.MSG_ERROR_INVALID_LOGIN)
            return False

        return super(LogInForm, self).is_valid()

    class Meta:
        model = User
        fields = ('username', 'password')


class MoveForm(forms.ModelForm):
    origin = forms.IntegerField(min_value=0, max_value=63, required=True)
    target = forms.IntegerField(min_value=0, max_value=63, required=True)

    class Meta:
        model = Move
        fields = ('origin', 'target')


class SignupForm(forms.Form):

    username = forms.CharField(required=True, label='', widget=TextInput(attrs={'class': ' form-style content__info text-center', 'placeholder': 'Usuario'}))
    password = forms.CharField(label='', min_length=6, required=True, widget=PasswordInput(attrs={'class': 'form-style content__info text-center', 'placeholder': 'Contraseña'}))
    password2 = forms.CharField(label='', min_length=6, required=True, widget=PasswordInput(attrs={'class': 'form-style content__info text-center', 'placeholder': 'Repetir contraseña'}))

    class Meta:
        model = User
        fields = ('username', 'password')
