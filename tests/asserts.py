
__all__ = (
    'assert_input',
    'refute_input',
    'assert_page_title',
    'assert_content_title',
    'assert_breadcrums_title',
    'assert_management_form_inputs',
    'refute_delete_button',
    'select_element',
)

def assert_input(response, name, value=None):
    '''
    Verify if the input with ``name`` exists in ``response``

    If value is not None, assert the input value is ``value``
    '''
    field = cssselect_input_or_textarea(response, name)

    if len(field) == 0:
        assert 0, 'No field found with name "{0}"'.format(name)
    if len(field) > 1:
        assert 0, 'Expected 1 field with name "{0}", found {1}'.format(name, len(field))

    if value is None:
        return

    field = field[0]

    if field.tag == 'input':
        try:
            found_value = field.attrib['value'].strip()
        except KeyError:
            if not value: # no value was expected here, so it's ok
                return
            assert 0, 'Field "{0}" has no value, expected "{1}"'.format(name, value)
    elif field.tag == 'textarea':
        found_value = field.text_content().strip()
    else:
        assert 0, 'Unexpected field type: {0}'.format(field.tag)

    assert found_value == str(value), 'Expected value="{0}" for field "{1}", found "{2}"'.format(
        value, name, found_value)

def refute_input(response, name):
    '''
    Make sure input with ``name`` doesn't exist in ``response``

    '''
    field = cssselect_input_or_textarea(response, name)

    if len(field) > 0:
        assert 0, 'Expected no fields with name "{0}", found {1}'.format(name, len(field))

def cssselect_input_or_textarea(response, name):
    field = response.lxml.cssselect('input[name={0}]'.format(name))
    if len(field) == 0:
        field = response.lxml.cssselect('textarea[name={0}]'.format(name))
    return field

def assert_page_title(response, title):
    elem = response.lxml.cssselect('title')
    assert elem[0].text_content().strip() == title

def assert_content_title(response, title):
    elem = response.lxml.cssselect('#content h1')
    assert len(elem) > 0, 'No titles found in content'
    assert elem[0].text_content().strip() == title

def assert_breadcrums_title(response, title):
    elem = response.lxml.cssselect('.breadcrumbs')
    assert len(elem) > 0, 'No .breadcrumbs found'
    assert title in elem[0].text_content()

def assert_management_form_inputs(response, total, initial, max_num):
    assert_input(response, name='comment_set-TOTAL_FORMS', value=total)
    assert_input(response, name='comment_set-INITIAL_FORMS', value=initial)
    assert_input(response, name='comment_set-MAX_NUM_FORMS', value=max_num)

def refute_delete_button(response):
    elem = response.lxml.cssselect('.submit-row .deletelink-box')
    assert len(elem) == 0, "Found delete button, should not exist"

def select_element(response, selector):
    elements = response.lxml.cssselect(selector)
    assert len(elements) == 1, "Expected 1 element for selector '{0}', found {1}".format(
            selector, len(elements))
    return elements[0]
