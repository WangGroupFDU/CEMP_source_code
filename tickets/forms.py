from django import forms

from .models import Ticket


class TicketCreateForm(forms.Form):

    subject = forms.CharField(
        max_length=200,
        label="Subject",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Briefly describe your issue or suggestion",
            }
        ),
    )
    category = forms.ChoiceField(
        choices=Ticket.CATEGORY_CHOICES,
        label="Category",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    priority = forms.ChoiceField(
        choices=Ticket.PRIORITY_CHOICES,
        label="Priority",
        initial=Ticket.PRIORITY_NORMAL,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    content = forms.CharField(
        label="Description",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Describe the context, steps to reproduce, expected behavior, or your suggestion.",
            }
        ),
    )

    def clean_content(self):

        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("Description cannot be empty.")
        return content


class TicketReplyForm(forms.Form):

    content = forms.CharField(
        label="Reply",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Add more details, upload context manually in text, or confirm whether the reply solves your issue.",
            }
        ),
    )

    def clean_content(self):

        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("Reply cannot be empty.")
        return content


class StaffTicketReplyForm(forms.Form):

    content = forms.CharField(
        label="Maintainer Reply",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 7,
                "placeholder": "Write the official reply that will be shown to the user inside CEMP.",
            }
        ),
    )

    def clean_content(self):

        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError("Reply cannot be empty.")
        return content
