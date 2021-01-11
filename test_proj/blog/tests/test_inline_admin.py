import pytest
from django.urls import reverse
from django_webtest import DjangoTestApp, WebTestMixin

from ..models import Article, Author


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


def test_actions_available(admin_client, author):
    """Test weather the action column is rendered."""
    url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(url)
    path = (
        './/div[@id="article_set-group"]//table'
        '//thead//th[starts-with(text(), "Actions")]'
    )
    assert len(changeview.lxml.xpath(path)) == 1

    url = reverse('admin:blog_author_add')
    addview = admin_client.get(url)
    assert len(addview.lxml.xpath(path)) == 1


def test_no_actions_on_none(admin_client, author):
    """If `inline_actions=None` no actions should be visible"""
    from ..admin import ArticleInline

    url = reverse('admin:blog_article_changelist')

    # save
    old_inlinec_actions = ArticleInline.inline_actions
    ArticleInline.inline_actions = None

    url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(url)
    path = (
        './/div[@id="article_set-group"]//table'
        '//thead//th[starts-with(text(), "Actions")]'
    )
    assert len(changeview.lxml.xpath(path)) == 0

    url = reverse('admin:blog_author_add')
    addview = admin_client.get(url)
    assert len(addview.lxml.xpath(path)) == 0

    # restore
    ArticleInline.inline_actions = old_inlinec_actions


def test_actions_methods_called(admin_client, mocker, article):
    """Test is all required methods are called."""
    from inline_actions.admin import InlineActionsMixin

    mocker.spy(InlineActionsMixin, 'render_inline_actions')
    mocker.spy(InlineActionsMixin, 'get_inline_actions')
    author = article.author

    url = reverse('admin:blog_author_change', args=(author.pk,))
    admin_client.get(url)

    assert InlineActionsMixin.render_inline_actions.call_count > 0
    assert InlineActionsMixin.get_inline_actions.call_count > 0


@pytest.mark.parametrize("action", ['view_action', 'publish', 'delete_action'])
def test_actions_rendered(admin_client, article, action):
    """Test wether all action buttons are rendered."""
    author = article.author

    url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(url)

    input_name = '_action__articleinline__inline__{}__blog__article__{}'.format(
        action, article.pk
    )
    assert input_name in dict(changeview.form.fields)


def test_publish_action(admin_client, mocker, article):
    """Test dynamically added actions using `get_actions()`"""
    from ..admin import UnPublishActionsMixin

    mocker.spy(UnPublishActionsMixin, 'get_inline_actions')
    mocker.spy(UnPublishActionsMixin, 'publish')
    mocker.spy(UnPublishActionsMixin, 'unpublish')
    author = article.author
    assert article.status == Article.DRAFT

    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    publish_input_name = (
        '_action__articleinline__inline__publish__blog__article__{}'.format(article.pk)
    )
    unpublish_input_name = (
        '_action__articleinline__inline__unpublish__blog__article__{}'.format(
            article.pk
        )
    )

    # open changeform
    changeview = admin_client.get(author_url)
    assert UnPublishActionsMixin.get_inline_actions.call_count > 0
    assert publish_input_name in dict(changeview.form.fields)

    # execute and test publish action
    changeview = changeview.form.submit(name=publish_input_name).follow()
    # not available in django 1.7
    # article.refresh_from_db()
    article = Article.objects.get(pk=article.pk)
    assert publish_input_name not in dict(changeview.form.fields)
    assert unpublish_input_name in dict(changeview.form.fields)
    assert UnPublishActionsMixin.publish.call_count == 1
    assert article.status == Article.PUBLISHED

    # execute and test unpublish action
    changeview = changeview.form.submit(name=unpublish_input_name).follow()
    # article.refresh_from_db()
    article = Article.objects.get(pk=article.pk)
    assert publish_input_name in dict(changeview.form.fields)
    assert unpublish_input_name not in dict(changeview.form.fields)
    assert UnPublishActionsMixin.unpublish.call_count == 1
    assert article.status == Article.DRAFT


def test_view_action(admin_client, mocker, article):
    """Test view action."""
    from inline_actions.actions import ViewAction

    mocker.spy(ViewAction, 'view_action')
    author = article.author

    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(author_url)

    # execute and test view action
    input_name = (
        '_action__articleinline__inline__view_action__blog__article__{}'.format(
            article.pk,
        )
    )
    response = changeview.form.submit(name=input_name).follow()
    assert ViewAction.view_action.call_count == 1
    article_url = reverse('admin:blog_article_change', args=(article.pk,))
    assert response.request.path == article_url


def test_delete_action_without_permission(admin_client, mocker, article):
    """Delete action should not be visible without permission."""
    from ..admin import ArticleInline

    mocker.patch.object(ArticleInline, 'has_delete_permission', return_value=False)
    author = article.author

    # mock delete_permission
    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(author_url)

    input_name = (
        '_action__articleinline__inline__delete_action__blog__article__{}'.format(
            article.pk,
        )
    )
    assert input_name not in dict(changeview.form.fields)


def test_delete_action(admin_client, mocker, article):
    """Test delete action."""
    from inline_actions.actions import DeleteAction

    mocker.spy(DeleteAction, 'delete_action')
    author = article.author

    # mock delete_permission
    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(author_url)

    # execute and test delete action
    input_name = (
        '_action__articleinline__inline__delete_action__blog__article__{}'.format(
            article.pk,
        )
    )
    response = changeview.form.submit(name=input_name).follow()
    assert DeleteAction.delete_action.call_count == 1
    assert response.request.path == author_url
    with pytest.raises(Article.DoesNotExist):
        Article.objects.get(pk=article.pk)


def test_handle_multiple_inlines(admin_client, mocker, article):
    """
    Test that we can have multiple inlines for the same model.
    """
    from ..admin import ArticleNoopInline

    mocker.spy(ArticleNoopInline, 'noop_action')
    author = article.author

    # mock delete_permission
    author_url = reverse('admin:blog_authorproxy_change', args=(author.pk,))
    changeview = admin_client.get(author_url)

    # run action on second inline
    input_name = (
        '_action__articlenoopinline__inline__noop_action__blog__article__{}'.format(
            article.pk,
        )
    )
    changeview.form.submit(name=input_name).follow()
    assert ArticleNoopInline.noop_action.call_count == 1
