from django.dispatch import Signal


light_save = Signal(providing_args=["request"])

