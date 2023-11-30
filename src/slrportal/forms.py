from django import forms
from api.models import Item


class ItemForm(forms.ModelForm):
    CATEGORY_CHOICES = [
        ('F', 'Food'),
        ('D', 'Drink'),
        ('O', 'Other'),
    ]

    person_id = forms.CharField(widget=forms.HiddenInput())
    claim = forms.BooleanField(label='Claim', initial=True, required=False)
    name = forms.CharField(label='Name', max_length=100)
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)
    quantity = forms.CharField(label='Quantity', required=False)
    description = forms.CharField(label='Description', widget=forms.Textarea, required=False)

    class Meta:
        model = Item
        fields = ['name', 'category', 'quantity', 'description']


class RsvpForm(forms.Form):
    CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
        ('M', 'Maybe'),
    ]

    person_id = forms.CharField(widget=forms.HiddenInput())
    rsvp = forms.ChoiceField(choices=CHOICES, label='RSVP')
