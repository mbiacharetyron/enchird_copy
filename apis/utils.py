import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _



def validate_password(password):
    """Docstring for function."""
    if len(password) < 8:
        raise ValueError("The password must be at least 8 characters")

    if not re.findall(r'\d', password):
        raise ValueError("The password must contain at least 1 digit, 0-9.")
            
    if not re.findall(r'[A-Z]', password):
        raise ValueError("The password must contain at least 1 uppercase letter, A-Z.")

    if not re.findall(r'[a-z]', password):
        raise ValueError("The password must contain at least 1 lowercase letter, a-z.")

    if not re.findall(r'[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', password):
        raise ValueError("The password must contain at least one symbol" +
                      "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?")

    return password


