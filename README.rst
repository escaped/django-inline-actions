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

.. image:: https://raw.githubusercontent.com/escaped/django-inline-actions/master/example_changelist.png

.. image:: https://raw.githubusercontent.com/escaped/django-inline-actions/master/example_inline.png


Installation
============

**Note**: For now only ``django<1.11`` is supported. Pull Requests are welcome!

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


Additionally, you can add methods to generate a custom label and css classes per object.
If you have an inline action called ``action_name`` then you can define ::

    def get_action_name_label(self, obj):
        return 'some string'


    def get_action_name_css(self, obj):
        return 'some string'


#. ``obj`` - instance on which the action was triggered

Each defined method has to return a string.



Example 1
=========
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


Adding ``inline_actions`` to the changelist works similar. See the sample project for
further details (``test_proj/blog/admin.py``).

Example 2
=========

If we want only one button, we can alternatively create single an
action ``toggle_publish`` that will be used to change the publish status. ::

    def toggle_publish(self, request, obj, parent_obj=None):
        if obj.status == Article.DRAFT:
            obj.status = Article.PUBLISHED
        else:
            obj.status = Article.DRAFT

        obj.save()
        status = 'unpublished' if obj.status == Article.DRAFT else 'published'
        messages.info(request, _("Article {}.".format(status)))

This might leave the user with an ambiguous button label as it will be called
``Toggle publish``. We can easily modify it by adding: ::

    def get_toggle_publish_label(self, obj):
        label = 'publish' if obj.status == Article.DRAFT else 'unpublish'
        return 'Toggle {}'.format(label)


So assuming an object in row has ``DRAFT`` status, then the button label will be
``Toggle publish`` and ``Toggle unpublish`` otherwise.

We can go even fancier when we create a method that will add css classes
for each object depending on a status like: ::


    def get_toggle_publish_css(self, obj):
        return (
            'btn-green' if obj.status == Article.DRAFT else 'btn-red')

You can make it more eye-candy by using ``btn-green`` that makes your button green and
``btn-red`` that makes your button red. Or zou can use those classes to add some
javascript logic (i.e. confirmation box).


Example Application
===================
You can see ``django-inline-actions`` in action using the bundled test application
``test_proj``. I recommend to use a ``virtualenv``. ::

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


Migration to 1.0.0
==================

Version 1.0.0 adds support for the admin changelist. Since the django ``ModelAdmin``
already has its own ``action`` handling, this release introduces **breaking changes**.
Basically ``action`` has been renamed to ``inline_action`` in all method and property
names.


+----------+----------------+-----------------------+
| type     | old_name       | new_name              |
+==========+================+=======================+
| property | actions        | inline_actions        |
+----------+----------------+-----------------------+
| method   | get_actions    | get_inline_actions    |
+----------+----------------+-----------------------+
| method   | render_actions | render_inline_actions |
+----------+----------------+-----------------------+


Since an action can now be called from a ``ModelAdmin`` or an ``InlineAdmin`` the signature
of each action has changed to ``def action_name(self, request, obj, parent_obj=None)``.
See `Integration`_ for further details.

If you do not want to use ``inline_actions`` on a changelist, you must deactivate
its rendering explicitly ::

      class Foo(InlineActionsModelAdminMixin, admin.ModelADmin):
         inline_actions = None
         # ...
