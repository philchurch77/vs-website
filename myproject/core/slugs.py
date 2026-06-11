from django.utils.text import slugify


def generate_unique_slug(instance, source_text, slug_field="slug"):
    """Build a slug from ``source_text``, appending -1, -2, … until unique.

    Uniqueness is checked against the instance's model, excluding the
    instance itself when it already has a primary key.
    """
    base_slug = slugify(source_text)
    slug = base_slug
    counter = 1
    queryset = type(instance).objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
