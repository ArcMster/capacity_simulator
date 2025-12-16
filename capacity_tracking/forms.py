from django import forms

class ScheduleUploadForm(forms.Form):
    schedule_file = forms.FileField(
        label='Select Schedule Image/PDF',
        help_text='Upload an image (PNG, JPG) or PDF of the vessel schedule.'
    )
