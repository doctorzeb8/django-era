from django import forms
from django.contrib.auth import get_user_model
from era import _, random_str
from .models import Confirm


user_field = get_user_model().USERNAME_FIELD
new_password_input = forms.PasswordInput(attrs={'placeholder': _('enter new password')})


class NonUniqueMixin:
    def validate_unique(self):
        pass


class LoginForm(NonUniqueMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'password')
        widgets = {'password': forms.PasswordInput()}


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = (user_field, 'name', 'password')
        widgets = {
            'email': forms.TextInput(attrs={'readonly': 'readonly'}),
            'password': new_password_input}


class JoinForm(NonUniqueMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = (user_field, 'name', 'password')
        widgets = {'password': forms.PasswordInput()}


class ResetForm(NonUniqueMixin, forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = (user_field, 'password')
        widgets = {'password': new_password_input}


class ConfirmForm(forms.ModelForm):
    class Meta:
        model = Confirm
        fields = ('code', 'sign')
        widgets = {'sign': forms.PasswordInput(
            attrs={'placeholder': _('enter password again')})}


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = (user_field, 'role', 'name', 'password', 'access')

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.fields['password'].required = False
        if self.instance.pk:
            self.fields['password'].widget = new_password_input
        else:
            self.fields['password'].widget = forms.PasswordInput({
                'placeholder': _('leave blank for random')})
