# django-inline-actions

[![pypi](https://img.shields.io/pypi/v/django-inline-actions.svg)](https://pypi.python.org/pypi/django-inline-actions) [![Build Status](https://travis-ci.org/escaped/django-inline-actions.png?branch=master)](http://travis-ci.org/escaped/django-inline-actions) [![Coverage](https://coveralls.io/repos/escaped/django-inline-actions/badge.png?branch=master)](https://coveralls.io/r/escaped/django-inline-actions) ![python version](https://img.shields.io/pypi/pyversions/django-inline-actions.svg) ![Project status](https://img.shields.io/pypi/status/django-inline-actions.svg) ![license](https://img.shields.io/pypi/l/django-inline-actions.svg)

django-inline-actions adds actions to the InlineModelAdmin and ModelAdmin changelist.


## Screenshot

![Changelist example](https://raw.githubusercontent.com/escaped/django-inline-actions/master/example_changelist.png)
![Inline example](https://raw.githubusercontent.com/escaped/django-inline-actions/master/example_inline.png)

## Installation

**NOTE** If you are on `django<2.0`, you have to use `django-inline-actions<2.0`.

1. Install django-inline-actions

    pip install django-inline-actions

2. Add `inline_actions` to your `INSTALLED_APPS`.


## Integration

Add the `InlineActionsModelAdminMixin` to your `ModelAdmin`.
If you want to have actions on your inlines, add the `InlineActionMixin` to your `InlineModelAdmin`.
Each action is implemented as a method on the `ModelAdmin`/`InlineModelAdmin` and **must have** the following signature.

    def action_name(self, request, obj, parent_obj=None):

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

    def get_action_name_label(self, obj):
        return 'some string'

    def get_action_name_css(self, obj):
        return 'some string'

| Argument | Description                                |
|----------|--------------------------------------------|
| `obj`    | instance on which the action was triggered |

Each defined method has to return a string.


### Example 1

Imagine a simple news application with the following `admin.py`.

    from django.contrib import admin
    from inline_actions.admin import InlineActionsMixin
    from inline_actions.admin import InlineActionsModelAdminMixin

    from .models import Article, Author


    class ArticleInline(InlineActionsMixin,
                        admin.TabularInline):
        model = Article
        inline_actions = []

        def has_add_permission(self):
            return False


    @admin.register(Author)
    class AuthorAdmin(InlineActionsModelAdminMixin,
                      admin.ModelAdmin):
        inlines = [ArticleInline]
        list_display = ('name',)


    @admin.register(Article)
    class AuthorAdmin(admin.ModelAdmin):
        list_display = ('title', 'status', 'author')


We now want to add two simple actions (`view`, `unpublish`) to each article within the `AuthorAdmin`.
The `view` action redirects to the changeform of the selected instance.

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

Since `unpublish` depends on `article.status` we must use `get_inline_actions` to add this action dynamically.

    from django.contrib import admin, messages
    from django.utils.translation import ugettext_lazy as _


    class ArticleInline(InlineActionsMixin,
                        admin.TabularInline):
        # ...
        def get_inline_actions(self, request, obj=None):
            actions = super(ArticleInline, self).get_inline_actions(request, obj)
            if obj:
                if obj.status == Article.PUBLISHED:
                    actions.append('unpublish')
            return actions

        def unpublish(self, request, obj, inline_obj):
            inline_obj.status = Article.DRAFT
            inline_obj.save()
            messages.info(request, _("Article unpublished"))
        unpublish.short_description = _("Unpublish")


Adding `inline_actions` to the changelist works similar. See the sample project for further details (`test_proj/blog/admin.py`).

### Example 2

Instead of creating separate actions for publishing and unpublishing, we might prefer an action, which toggles between those two states.
`toggle_publish` implements the behaviour described above.

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

This might leave the user with an ambiguous button label as it will be called `Toggle publish` regardless of the internal state.
We can specify a dynamic label by adding a special method `get_ACTIONNAME_label`.

    def get_toggle_publish_label(self, obj):
        if obj.status == Article.DRAFT:
            return 'Publish'
        return 'Unpublish'


So assuming an object in a row has `DRAFT` status, then the button label will be `Toggle publish` and `Toggle unpublish` otherwise.

We can go even fancier when we create a method that will add css classes for each object depending on a status like:


    def get_toggle_publish_css(self, obj):
        if obj.status == Article.DRAFT:
            return 'btn-red'
        return 'btn-green'

You can make it more eye-candy by using `btn-green` that makes your button green and `btn-red` that makes your button red.
Or you can use those classes to add some javascript logic (i.e. confirmation box).


## Example Application

You can see `django-inline-actions` in action using the bundled test application `test_proj`.
Use [`poetry`](https://poetry.eustace.io/) to run it.

    git clone https://github.com/escaped/django-inline-actions.git
    cd django-inline-actions/
    poetry install
    poetry run pip install Django
    cd test_proj
    poetry run ./manage.py migrate
    poetry run ./manage.py createsuperuser
    poetry run ./manage.py runserver

Open [`http://localhost:8000/admin/`](http://localhost:8000/admin/) in your browser and create an author and some articles.
