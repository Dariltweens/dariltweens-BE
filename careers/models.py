"""Careers models.

A Job is admin-managed and shown publicly only while ``published``. Applications
are handled entirely off-platform (the frontend opens the applicant's email app),
so there is no application model here by design. The slug is derived from the
title on first save so the admin API never has to supply one.
"""

from django.db import models
from django.utils.text import slugify

from careers.enums import EmploymentType, JobStatus


class Job(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    department = models.CharField(max_length=120, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PUBLISHED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self) -> str:
        base = slugify(self.title) or "job"
        slug = base
        n = 2
        qs = Job.objects.exclude(pk=self.pk)
        while qs.filter(slug=slug).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug
