from django.core.exceptions import ValidationError

MAX_UPLOAD_MB = 20


def validate_upload_size(file):
    if file.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f"File is too large (max {MAX_UPLOAD_MB} MB).")
