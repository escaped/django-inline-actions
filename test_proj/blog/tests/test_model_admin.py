import pytest
from django.urls import reverse

from ..models import Article


def test_actions_available(admin_client, article):
    """Test weather the action column is rendered."""
    url = reverse('admin:blog_article_changelist')
    changeview = admin_client.get(url)
    path = (
        './/table[@id="result_list"]' '//thead//th//*[starts-with(text(), "Actions")]'
    )
    assert len(changeview.lxml.xpath(path)) == 1


def test_no_actions_on_none(admin_client, article):
    """If `inline_actions=None` no actions should be visible"""
    from ..admin import ArticleAdmin

    url = reverse('admin:blog_article_changelist')

    # save
    old_inlinec_actions = ArticleAdmin.inline_actions
    ArticleAdmin.inline_actions = None

    changeview = admin_client.get(url)
    path = (
        './/table[@id="result_list"]' '//thead//th//*[starts-with(text(), "Actions")]'
    )
    assert len(changeview.lxml.xpath(path)) == 0

    # restore
    ArticleAdmin.inline_actions = old_inlinec_actions


def test_actions_methods_called(admin_client, mocker, article):
    """Test is all required methods are called."""
    from inline_actions.admin import BaseInlineActionsMixin

    mocker.spy(BaseInlineActionsMixin, 'render_inline_actions')
    mocker.spy(BaseInlineActionsMixin, 'get_inline_actions')

    url = reverse('admin:blog_article_changelist')
    admin_client.get(url)

    assert BaseInlineActionsMixin.render_inline_actions.call_count > 0
    assert BaseInlineActionsMixin.get_inline_actions.call_count > 0


def test_actions_dynamic_label_called(admin_client, mocker, article):
    """Test that if for <method> model admin contains 'get_<method>_label
    then this method will be called
    """

    from ..admin import TogglePublishActionsMixin

    mocker.spy(TogglePublishActionsMixin, 'get_toggle_publish_label')

    url = reverse('admin:blog_article_changelist')
    admin_client.get(url)

    assert TogglePublishActionsMixin.get_toggle_publish_label.call_count > 0


def test_actions_dynamic_css_called(admin_client, mocker, article):
    """Test that if for <method> model admin contains 'get_<method>_css
    then this method will be called
    """

    from ..admin import TogglePublishActionsMixin

    mocker.spy(TogglePublishActionsMixin, 'get_toggle_publish_css')

    url = reverse('admin:blog_article_changelist')
    admin_client.get(url)

    assert TogglePublishActionsMixin.get_toggle_publish_css.call_count > 0


@pytest.mark.parametrize('action', ['view_action', 'publish'])
def test_actions_rendered(admin_client, article, action):
    """Test wether all action buttons are rendered."""
    url = reverse('admin:blog_article_changelist')
    changelist = admin_client.get(url)

    input_name = '_action__articleadmin__admin__{}__blog__article__{}'.format(
        action, article.pk
    )
    assert input_name in dict(changelist.form.fields)


def test_publish_action(admin_client, mocker, article):
    """Test dynamically added actions using `get_actions()`"""
    from ..admin import UnPublishActionsMixin

    mocker.spy(UnPublishActionsMixin, 'get_inline_actions')
    mocker.spy(UnPublishActionsMixin, 'publish')
    mocker.spy(UnPublishActionsMixin, 'unpublish')
    assert article.status == Article.DRAFT

    article_url = reverse('admin:blog_article_changelist')
    publish_input_name = (
        '_action__articleadmin__admin__publish__blog__article__{}'.format(article.pk)
    )
    unpublish_input_name = (
        '_action__articleadmin__admin__unpublish__blog__article__{}'.format(
            article.pk,
        )
    )

    # open changelist
    changelist = admin_client.get(article_url)
    assert UnPublishActionsMixin.get_inline_actions.call_count > 0
    assert publish_input_name in dict(changelist.form.fields)

    # execute and test publish action
    changelist = changelist.form.submit(name=publish_input_name).follow()
    # not available in django 1.7
    # article.refresh_from_db()
    article = Article.objects.get(pk=article.pk)
    assert publish_input_name not in dict(changelist.form.fields)
    assert unpublish_input_name in dict(changelist.form.fields)
    assert UnPublishActionsMixin.publish.call_count == 1
    assert article.status == Article.PUBLISHED

    # execute and test unpublish action
    changelist = changelist.form.submit(name=unpublish_input_name).follow()
    # article.refresh_from_db()
    article = Article.objects.get(pk=article.pk)
    assert publish_input_name in dict(changelist.form.fields)
    assert unpublish_input_name not in dict(changelist.form.fields)
    assert UnPublishActionsMixin.unpublish.call_count == 1
    assert article.status == Article.DRAFT


def test_view_action(admin_client, mocker, article):
    """Test view action."""
    from inline_actions.actions import ViewAction

    mocker.spy(ViewAction, 'view_action')

    article_url = reverse('admin:blog_article_changelist')
    changeview = admin_client.get(article_url)

    # execute and test view action
    input_name = '_action__articleadmin__admin__view_action__blog__article__{}'.format(
        article.pk
    )
    response = changeview.form.submit(name=input_name).follow()
    assert ViewAction.view_action.call_count == 1
    article_change_url = reverse('admin:blog_article_change', args=(article.pk,))
    assert response.request.path == article_change_url


def test_no_actions_on_changelist(admin_client, article):
    """Test wether the actions fields is hidden by default"""
    url = reverse('admin:blog_article_change', args=(article.pk,))
    changelist = admin_client.get(url)

    assert 'field-render_inline_actions' not in changelist.content.decode('utf8')
