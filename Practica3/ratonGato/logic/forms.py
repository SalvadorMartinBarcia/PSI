from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from datamodel.models import Game, Move, UserProfile
from datamodel import constants


class LogInForm(AuthenticationForm):
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
    username = forms.CharField(required=True, label="Nombre")
    password = forms.CharField(label='Contraseña', min_length=6, required=True, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Contraseña', min_length=6, required=True, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'password')
