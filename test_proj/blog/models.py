from django.db import models
from django.utils.translation import gettext_lazy as _


class Author(models.Model):
    name = models.CharField(
        max_length=50,
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    DRAFT = 'draft'
    PUBLISHED = 'published'

    STATUS_CHOICES = (
        (DRAFT, _("Draft")),
        (PUBLISHED, _("Published")),
    )

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField(
        max_length=100,
    )
    body = models.TextField()
    status = models.CharField(
        choices=STATUS_CHOICES,
        default=DRAFT,
        max_length=10,
    )

    def __str__(self):
        return self.title


class AuthorProxy(Author):
    class Meta:
        proxy = True
