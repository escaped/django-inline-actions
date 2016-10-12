=====================
django-inline-actions
=====================



.. image:: https://img.shields.io/pypi/v/django-inline-actions.svg
    :target: https://pypi.python.org/pypi/django-inline-actions

.. image:: https://travis-ci.org/escaped/django-inline-actions.png?branch=master
    :target: http://travis-ci.org/escaped/django-inline-actions
    :alt: Build Status

.. image:: https://coveralls.io/repos/escaped/django-inline-actions/badge.png?branch=master
    :target: https://coveralls.io/r/escaped/django-inline-actions
    :alt: Coverage

.. image:: https://img.shields.io/pypi/pyversions/django-inline-actions.svg

.. image:: https://img.shields.io/pypi/status/django-inline-actions.svg

.. image:: https://img.shields.io/pypi/l/django-inline-actions.svg


django-inline-actions adds actions to the InlineModelAdmin and ModelAdmin changelist.


Screenshot
==========

.. image:: https://raw.githubusercontent.com/escaped/django-inline-actions/master/example.png


Installation
============

#. Install django-inline-actions ::

    pip install django-inline-actions

#. Add ``inline_actions`` to your ``INSTALLED_APPS``.


Integration
===========

Add the ``InlineActionsModelAdminMixin`` to your ``ModelAdmin``.
If you want to have actions on your inlines, add the ``InlineActionMixin`` to your
``InlineModelAdmin``.
Each action is implemented as a method on the ``ModelAdmin``/``InlineModelAdmin`` and has
the following signature ::

    def action_name(self, request, obj, parent_obj=None)

#. ``request`` - current request
#. ``obj`` - instance on which the action was triggered
#. ``parent_obj`` - instance of the parent model, only set on inlines

and should return ``None`` to return to the current changeform or a ``HttpResponse``.
Finally, add your method name to the ``inline_actions`` property.
If you want to disable the ``Actions`` column, explicitly set `inline_actions = None`.
To add your actions dynamically, you can use the method
``get_inline_actions(self, request, obj=None)`` instead.


This module is bundled with two actions for viewing
(``inline_actions.actions.ViewAction``) and deleting
(``inline_actions.actions.DeleteAction``).
Just add these classes to your admin and you're done.

Example
=======
Imagine a simple news application with the following ``admin.py``. ::

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


We now want to add two simple actions (``view``, ``unpublish``) to
each article within the ``AuthorAdmin``.
The ``view`` action redirects to the changeform of the selected instance ::

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


Since ``unpublish`` depends on ``article.status`` we must use ``get_inline_actions`` to
add this action dynamically. ::

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


Adding `inline_actions` to the changelist works similar. See the sample project for
further details (`test_proj/blog/admin.py`).


Example Application
===================
You can see ``django-inline-actions`` in action using the bundled test application
``test_proj``. I recommend to use a `virtualenv`. ::

   git clone https://github.com/escaped/django-inline-actions.git
   cd django-inline-actions/
   pip install Django
   pip install -e .
   cd test_proj
   ./manage.py migrate
   ./manage.py createsuperuser
   ./manage.py runserver

Open `<http://localhost:8000/admin/>`_ in your browser and create an
author and some articles.
