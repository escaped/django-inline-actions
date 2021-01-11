import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_changetitle_action(admin_client, mocker, article):
    """Test action with intermediate form."""
    new_title = 'Fooo bar!'
    action_name = (
        '_action__articleadmin__admin__change_title__blog__article__{}'.format(
            article.pk
        )
    )

    article_url = reverse('admin:blog_article_changelist')
    changeview = admin_client.get(article_url)

    changetitle_view = changeview.form.submit(name=action_name)
    assert changetitle_view.status_code == 200

    # action should be available as hidden field
    expected_field = '<input type="hidden" name="{}" value="">'.format(action_name)
    assert expected_field in changetitle_view.text

    # change title and save
    changetitle_view.form['title'] = new_title
    response = changetitle_view.form.submit(name='_save')
    response = response.follow()
    assert response.status_code == 200

    article.refresh_from_db()
    assert article.title == new_title
