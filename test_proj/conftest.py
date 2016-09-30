import pytest

from django_webtest import DjangoTestApp, WebTestMixin

from test_proj.blog.models import Article, Author


@pytest.fixture(scope='function')
def app(request):
    """WebTest's TestApp.
    Patch and unpatch settings before and after each test.
    WebTestMixin, when used in a unittest.TestCase, automatically calls
    _patch_settings() and _unpatchsettings.
    """
    wtm = WebTestMixin()
    wtm._patch_settings()
    request.addfinalizer(wtm._unpatch_settings)
    return DjangoTestApp()


@pytest.fixture()
def admin_client(app, admin_user):
    app.set_user(admin_user)
    return app


@pytest.fixture
def author():
    author, __ = Author.objects.get_or_create(
        name='Author',
    )
    return author


@pytest.fixture
def article(author):
    return Article.objects.create(
        author=author,
        body='Body lorem ipson dolor',
        title='Lorem ipson dolor',
    )
