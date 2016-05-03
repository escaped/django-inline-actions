import django
from pkg_resources import parse_version


if parse_version(django.get_version()) < parse_version('1.9'):
    class InlineAdminCompat(object):
        def get_fieldsets(self, request, obj=None):
            """Override method, since we do not support `declared_fieldsets` in
            django 1.8. This behavior is the default as of django 1.9.
            """
            if self.fieldsets:
                return self.fieldsets
            return [(None, {'fields': self.get_fields(request, obj)})]
else:
    class InlineAdminCompat(object):
        pass
