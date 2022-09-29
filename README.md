# django-inline-actions

![PyPI](https://img.shields.io/pypi/v/django-inline-actions?style=flat-square)
![GitHub Workflow Status (master)](https://img.shields.io/github/workflow/status/escaped/django-inline-actions/Test%20&%20Lint/master?style=flat-square)
![Coveralls github branch](https://img.shields.io/coveralls/github/escaped/django-inline-actions/master?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-inline-actions?style=flat-square)
![PyPI - License](https://img.shields.io/pypi/l/django-inline-actions?style=flat-square)

django-inline-actions adds actions to each row of the ModelAdmin or InlineModelAdmin.

## Requirements

* Python 3.8 or newer

## Screenshot

![Changelist example](https://raw.githubusercontent.com/escaped/django-inline-actions/master/example_changelist.png)
![Inline example](https://raw.githubusercontent.com/escaped/django-inline-actions/master/example_inline.png)

## Installation

1. Install django-inline-actions

   ```sh
   pip install django-inline-actions
   ```

2. Add `inline_actions` to your `INSTALLED_APPS`.

## Integration

Add the `InlineActionsModelAdminMixin` to your `ModelAdmin`.
If you want to have actions on your inlines, add the `InlineActionsMixin` to your `InlineModelAdmin`.
Each action is implemented as a method on the `ModelAdmin`/`InlineModelAdmin` and **must have** the following signature.

```python
def action_name(self, request, obj, parent_obj=None):
```

| Argument     | Description                                       |
|--------------|---------------------------------------------------|
| `request`    | current request                                   |
| `obj`        | instance on which the action was triggered        |
| `parent_obj` | instance of the parent model, only set on inlines |

and should return `None` to return to the current changeform or a `HttpResponse`.
Finally, add your method name to list of actions `inline_actions` defined on the corresponding `ModelAdmin`.
If you want to disable the *actions* column, you have to explicitly set `inline_actions = None`.
To add your actions dynamically, you can use the method `get_inline_actions(self, request, obj=None)` instead.

This module is bundled with two actions for viewing (`inline_actions.actions.ViewAction`) and deleting (`inline_actions.actions.DeleteAction`).
Just add these classes to your admin and you're done.

Additionally, you can add methods to generate a custom label and CSS classes per object.
If you have an inline action called `action_name` then you can define

```python
def get_action_name_label(self, obj):
    return 'some string'

def get_action_name_css(self, obj):
    return 'some string'
```

| Argument | Description                                |
|----------|--------------------------------------------|
| `obj`    | instance on which the action was triggered |

Each defined method has to return a string.

### Example 1

Imagine a simple news application with the following `admin.py`.

```python
from django.contrib import admin
from inline_actions.admin import InlineActionsMixin
from inline_actions.admin import InlineActionsModelAdminMixin

from .models import Article, Author


class ArticleInline(InlineActionsMixin,
                    admin.TabularInline):
    model = Article
    inline_actions = []

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Author)
class AuthorAdmin(InlineActionsModelAdminMixin,
                  admin.ModelAdmin):
    inlines = [ArticleInline]
    list_display = ('name',)


@admin.register(Article)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author')
```

We now want to add two simple actions (`view`, `unpublish`) to each article within the `AuthorAdmin`.
The `view` action redirects to the changeform of the selected instance.

```python
from django.core.urlresolvers import reverse
from django.shortcuts import redirect


class ArticleInline(InlineActionsMixin,
                    admin.TabularInline):
    # ...
    inline_actions = ['view']
    # ...

    def view(self, request, obj, parent_obj=None):
        url = reverse(
            'admin:{}_{}_change'.format(
                obj._meta.app_label,
                obj._meta.model_name,
            ),
            args=(obj.pk,)
        )
        return redirect(url)
    view.short_description = _("View")
```

Since `unpublish` depends on `article.status` we must use `get_inline_actions` to add this action dynamically.

```python
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _


class ArticleInline(InlineActionsMixin,
                    admin.TabularInline):
    # ...
    def get_inline_actions(self, request, obj=None):
        actions = super(ArticleInline, self).get_inline_actions(request, obj)
        if obj:
            if obj.status == Article.PUBLISHED:
                actions.append('unpublish')
        return actions

    def unpublish(self, request, obj, parent_obj=None):
        obj.status = Article.DRAFT
        obj.save()
        messages.info(request, _("Article unpublished"))
    unpublish.short_description = _("Unpublish")
```

Adding `inline_actions` to the changelist works similar. See the sample project for further details (`test_proj/blog/admin.py`).

### Example 2

Instead of creating separate actions for publishing and unpublishing, we might prefer an action, which toggles between those two states.
`toggle_publish` implements the behaviour described above.

```python
def toggle_publish(self, request, obj, parent_obj=None):
    if obj.status == Article.DRAFT:
        obj.status = Article.PUBLISHED
    else:
        obj.status = Article.DRAFT

    obj.save()

    if obj.status == Article.DRAFT:
        messages.info(request, _("Article unpublished."))
    else:
        messages.info(request, _("Article published."))
```

This might leave the user with an ambiguous button label as it will be called `Toggle publish` regardless of the internal state.
We can specify a dynamic label by adding a special method `get_ACTIONNAME_label`.

```python
def get_toggle_publish_label(self, obj):
    if obj.status == Article.DRAFT:
        return 'Publish'
    return 'Unpublish'
```

So assuming an object in a row has `DRAFT` status, then the button label will be `Toggle publish` and `Toggle unpublish` otherwise.

We can go even fancier when we create a method that will add css classes for each object depending on a status like:

```python
def get_toggle_publish_css(self, obj):
    if obj.status == Article.DRAFT:
        return 'btn-red'
    return 'btn-green'
```

You can make it more eye-candy by using `btn-green` that makes your button green and `btn-red` that makes your button red.
Or you can use those classes to add some javascript logic (i.e. confirmation box).

### Tip on confirmation alerts

When performing a certain critical action or ones which may not be easily reversible it's good to have a confirmation prompt before submitting the action form. To achieve this, one way would be to override `templates/admin/change_list.html` with the following.

```html
{% extends "admin/change_list.html" %}

{% block extrahead %}
    {{ block.super }}
    <script>
        (function() {
            document.addEventListener("DOMContentLoaded", function(event) {
                let inline_actions = document.querySelectorAll(".inline_actions input");
                for (var i=0; i < inline_actions.length; i++) {
                    inline_actions[i].addEventListener("click", function(e) {
                        if(!confirm("Do you really want to " + e.target.value + "?")) {
                            e.preventDefault();
                        }
                    });
                }
            });
        })();
    </script>
{% endblock %}
```

If a staff user has clicked any inline action accidentally, they can safely click no in the confirmation prompt & the inline action form would not be submitted.

## Intermediate forms

The current implementation for using intermediate forms involves some manual handling.
This will be simplified in the next major release!


In order to have an intermediate form, you must add some information about the triggered action.
`django-inline-actions` provides a handy templatetag `render_inline_action_fields`,
which adds these information as hidden fields to a form.

```html
{% extends "admin/base_site.html" %}
{% load inline_action_tags %}

{% block content %}
  <form action="" method="post">
    {% csrf_token %}
    {% render_inline_action_fields %}

    {{ form.as_p }}

    <input type="submit" name="_back" value="Cancel"/>
    <input type="submit" name="_save" value="Update"/>
  </form>
{% endblock %}
```

As the action does not know that an intermediate form is used, we have to include some special handling.
In the case above we have to consider 3 cases:

1. The form has been submitted and we want to redirect to the previous view.
2. Back button has been clicked.
3. Initial access to the intermediate page/form.

The corresponding action could look like

```python
    def change_title(self, request, obj, parent_obj=None):

        # 1. has the form been submitted?
        if '_save' in request.POST:
            form = forms.ChangeTitleForm(request.POST, instance=obj)
            form.save()
            return None  # return back to list view
        # 2. has the back button been pressed?
        elif '_back' in request.POST:
            return None  # return back to list view
        # 3. simply display the form
        else:
            form = forms.ChangeTitleForm(instance=obj)

        return render(
            request,
            'change_title.html',
            context={'form': form}
        )
```

## Example Application

You can see `django-inline-actions` in action using the bundled test application `test_proj`.
Use [`poetry`](https://poetry.eustace.io/) to run it.

```bash
git clone https://github.com/escaped/django-inline-actions.git
cd django-inline-actions/
poetry install
poetry run pip install Django
cd test_proj
poetry run ./manage.py migrate
poetry run ./manage.py createsuperuser
poetry run ./manage.py runserver
```

Open [`http://localhost:8000/admin/`](http://localhost:8000/admin/) in your browser and create an author and some articles.

## How to test your actions?

There are two ways on how to write tests for your actions.
We will use [pytest](https://docs.pytest.org/en/latest/) for the following examples.

### Test the action itself

Before we can call our action on the admin class itself, we have to instantiate the admin environment and pass it to the `ModelAdmin` together with an instance of our model.
Therefore, we implement a fixture called `admin_site`, which is used on each test.

```python
import pytest
from django.contrib.admin import AdminSite

from yourapp.module.admin import MyAdmin


@pytest.fixture
def admin_site():
    return AdminSite()

@pytest.mark.django_db
def test_action_XXX(admin_site):
    """Test action XXX"""
    fake_request = {}  # you might need to use a RequestFactory here
    obj = ...  # create an instance

    admin = MyAdmin(obj, admin_site)

    admin.render_inline_actions(article)
    response = admin.action_XXX(fake_request, obj)
    # assert the state of the application
```

### Test the admin integration

Alternatively, you can test your actions on the real Django admin page.
You will have to log in, navigate to the corresponding admin and trigger a click on the action.
To simplify this process you can use [django-webtest](https://github.com/django-webtest/django-webtest).
Example can be found [here](https://github.com/escaped/django-inline-actions/blob/76b6f6b83c6d1830c2ad71512cd1e85362936dbd/test_proj/blog/tests/test_inline_admin.py#L146).

## Development

This project uses [poetry](https://poetry.eustace.io/) for packaging and
managing all dependencies and [pre-commit](https://pre-commit.com/) to run
[flake8](http://flake8.pycqa.org/), [isort](https://pycqa.github.io/isort/),
[mypy](http://mypy-lang.org/) and [black](https://github.com/python/black).

Additionally, [pdbpp](https://github.com/pdbpp/pdbpp) and [better-exceptions](https://github.com/qix-/better-exceptions) are installed to provide a better debugging experience.
To enable `better-exceptions` you have to run `export BETTER_EXCEPTIONS=1` in your current session/terminal.

Clone this repository and run

```bash
poetry install
poetry run pre-commit install
```

to create a virtual enviroment containing all dependencies.
Afterwards, You can run the test suite using

```bash
poetry run pytest
```

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/)
style.

### Cookiecutter template

This project was created using [cruft](https://github.com/cruft/cruft) and the
[cookiecutter-pyproject](https://github.com/escaped/cookiecutter-pypackage) template.
In order to update this repository to the latest template version run

```sh
cruft update
```

in the root of this repository.
