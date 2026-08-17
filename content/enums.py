"""Content enumerations.

Dependency-free leaf module so any layer can import without circular-import risk.
"""

from django.db import models


class ArticleStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
