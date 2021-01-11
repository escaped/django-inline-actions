import pytest

from inline_actions.templatetags.inline_action_tags import render_inline_action_fields


def test_mulitple_actions_are_triggered(rf):
    request = rf.post(
        '/some/url/',
        data={
            '_action__admin__NAME1__blog__blog__1': "",
            '_action__admin__NAME2__blog__blog__1': "",
        },
    )
    context = {'request': request}

    with pytest.raises(RuntimeError) as exc_info:
        render_inline_action_fields(context)
    exception = exc_info.value
    assert (
        str(exception) == "Multiple inline actions have been triggered simultaneously."
    )


def test_no_action_is_triggered(rf):
    request = rf.post(
        '/some/url/',
    )
    context = {'request': request}

    with pytest.raises(RuntimeError) as exc_info:
        render_inline_action_fields(context)
    exception = exc_info.value
    assert str(exception) == "No inline action has been triggered."


def test_render_action(rf):
    action_name = '_action__admin__NAME1__blog__blog__1'
    request = rf.post(
        '/some/url/',
        data={
            '{}'.format(action_name): "",
        },
    )
    context = {'request': request}

    content = render_inline_action_fields(context)
    expected_content = '<input type="hidden" name="{}" value="">'.format(action_name)
    assert content == expected_content
