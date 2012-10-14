# coding: utf-8

from django.forms import CharField, ModelChoiceField, ModelMultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple
from registration.forms import RegistrationFormUniqueEmail
from django.utils.translation import ugettext_lazy as _
from .models import StudentProfile
from registration.models import RegistrationProfile
from django.contrib.auth.models import User, Group
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Reset, Fieldset
from crispy_forms.bootstrap import PrependedText, FormActions
from django.contrib.sites.models import get_current_site
from django.template.loader import render_to_string


def get_professors():
    return User.objects.filter(is_superuser=True)


def get_groups():
    return Group.objects.all()


class UserField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() or unicode(u)


class UserRegistrationForm(RegistrationFormUniqueEmail):
    first_name = CharField(label=_(u'Prénom(s)'))
    last_name = CharField(label=_('Nom'))
    professor = UserField(queryset=get_professors(), label=_('Professeur'))
    groups = ModelMultipleChoiceField(queryset=get_groups(),
                             widget=CheckboxSelectMultiple, label=_('Groupes'))

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Fieldset(
                _(u'Général'),
                Field('first_name', 'last_name', css_class='input-xlarge'),
                PrependedText('email', '@', active=True),
            ),
            Fieldset(
                _('Utilisateur'),
                'username',
                'password1', 'password2',
            ),
            Fieldset(
                _(u'Étudiant'),
                'professor',
                'groups',
            ),
            FormActions(
                Submit('save_changes', _('Enregistrer'), css_class="btn-primary"),
                Reset('reset', _(u'Réinitialiser')),
            ),
        )
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

    def save(self, profile_callback=None):
        data = self.cleaned_data
        new_user = RegistrationProfile.objects.create_inactive_user(
            username=data['username'],
            password=data['password1'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'])
        professor = data['professor']
        new_profile = StudentProfile(
            user=new_user,
            professor=professor,
            groups=data['groups'])
        new_profile.save()

        site_url = 'http://' + get_current_site(self.request).domain
        email_content = render_to_string(
            'accounts/grant_to_admin_demand_email.txt',
            {'user': new_profile.user, 'site_url': site_url})

        professor.email_user(_(u'Demande d’accès étudiant'),
            email_content)
