from django.contrib.auth.models import User
from django.contrib.admin import site as default_admin_site
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied

from django_webtest import WebTest
import mock
import pytest

from sampleproject.posts.models import Post, Comment
from modelclone import ClonableModelAdmin


class ClonableModelAdminTests(WebTest):

    def setUp(self):
        User.objects.create_superuser(
            username='admin',
            password='admin',
            email='admin@sampleproject.com'
        )

        self.post = Post.objects.create(
            title = 'How to learn windsurf',
            content = 'Practice a lot!',
        )

        self.post_with_comments = Post.objects.create(
            title = 'How to learn Django',
            content = 'Read https://docs.djangoproject.com/'
        )
        Comment.objects.create(
            author = 'Bob',
            content = 'Thanks! It really helped',
            post = self.post_with_comments
        )
        Comment.objects.create(
            author = 'Alice',
            content = 'Oh, really?!',
            post = self.post_with_comments
        )

        self.post_url = '/admin/posts/post/{0}/clone/'.format(
            self.post.id)
        self.post_with_comments_url = '/admin/posts/post/{0}/clone/'.format(
            self.post_with_comments.id)

    def test_clone_view_is_wrapped_as_admin_view(self):
        model = mock.Mock()
        admin_site = mock.Mock()
        admin_site.admin_view.return_value = '<wrapped clone view>'

        model_admin = ClonableModelAdmin(model, admin_site)
        clone_view_urlpattern = model_admin.get_urls()[0]

        assert '<wrapped clone view>' == clone_view_urlpattern.callback

    def test_clone_view_url_name(self):
        post_id = self.post.id
        expected_url = '/admin/posts/post/{0}/clone/'.format(post_id)

        assert reverse('admin:posts_post_clone', args=(post_id,)) == expected_url

    def test_clone_link_method_for_list_display_renders_object_clone_url(self):
        model_admin = ClonableModelAdmin(Post, default_admin_site)
        expected_link = '<a href="{0}">{1}</a>'.format(
            reverse('admin:posts_post_clone', args=(self.post.id,)),
            model_admin.clone_verbose_name)

        assert model_admin.clone_link(self.post) == expected_link

    def test_clone_link_methods_for_list_display_should_allow_tags_and_have_short_description(self):
        assert ClonableModelAdmin.clone_link.allow_tags is True
        assert ClonableModelAdmin.clone_link.short_description == \
               ClonableModelAdmin.clone_verbose_name

    def test_clone_should_display_clone_verbose_name_as_title(self):
        response = self.app.get(self.post_url, user='admin')

        # default value
        assert 'Duplicate' == ClonableModelAdmin.clone_verbose_name

        # customized value in sampleproject/posts/admin.py
        assert_page_title(response, 'Clone it! post | Django site admin')
        assert_content_title(response, 'Clone it! post')
        assert_breadcrums_title(response, 'Clone it! post')

    def test_clone_should_raise_permission_denied(self):
        model_admin = ClonableModelAdmin(Post, default_admin_site)
        model_admin.has_add_permission = mock.Mock(return_value=False)

        request = object()
        object_id = object()

        with pytest.raises(PermissionDenied):
            model_admin.clone_view(request, object_id)

        model_admin.has_add_permission.assert_called_once_with(request)

    # clone object

    def test_clone_should_pre_fill_all_form_fields(self):
        response = self.app.get(self.post_url, user='admin')

        # post
        assert_input(response, name='title', value='How to learn windsurf')
        assert_input(response, name='content', value='Practice a lot!')

        # csrf
        assert_input(response, name='csrfmiddlewaretoken')


    def test_clone_should_create_new_object_on_POST(self):
        response = self.app.get(self.post_url, user='admin')
        response.form.submit()

        assert 2 == Post.objects.filter(title=self.post.title).count()


    def test_clone_should_return_404_if_object_does_not_exist(self):
        response = self.app.get('/admin/posts/post/999999999/clone/', user='admin',
                                expect_errors=True)
        assert 404 == response.status_code

    # clone object with inlines

    def test_clone_should_pre_fill_all_form_fields_including_inlines_on_GET(self):
        response = self.app.get(self.post_with_comments_url, user='admin')

        # management form data
        assert_management_form_inputs(response, total=4, initial=0, max_num='')

        # comment 1
        assert_input(response, name='comment_set-0-author', value='Bob')
        assert_input(response, name='comment_set-0-content', value='Thanks! It really helped')
        assert_input(response, name='comment_set-0-id', value='')
        assert_input(response, name='comment_set-0-post', value='')
        assert_input(response, name='comment_set-0-DELETE', value='')

        # comment 2
        assert_input(response, name='comment_set-1-author', value='Alice')
        assert_input(response, name='comment_set-1-content', value='Oh, really?!')
        assert_input(response, name='comment_set-1-id', value='')
        assert_input(response, name='comment_set-1-post', value='')
        assert_input(response, name='comment_set-1-DELETE', value='')

        # first extra
        assert_input(response, name='comment_set-2-author', value='')
        assert_input(response, name='comment_set-2-content', value='')
        assert_input(response, name='comment_set-2-id', value='')
        assert_input(response, name='comment_set-2-post', value='')
        refute_input(response, name='comment_set-2-DELETE')

        # second extra
        assert_input(response, name='comment_set-3-author', value='')
        assert_input(response, name='comment_set-3-content', value='')
        assert_input(response, name='comment_set-3-id', value='')
        assert_input(response, name='comment_set-3-post', value='')
        refute_input(response, name='comment_set-3-DELETE')


    def test_clone_with_inlines_should_display_the_necessary_number_of_forms(self):
        extra = 2   # CommentInline.extra on sampleproject/posts

        for i in range(4):
            Comment.objects.create(
                author = 'Author ' + str(i),
                content = 'Content ' + str(i),
                post = self.post,
            )

        response = self.app.get(self.post_url, user='admin')

        for i in range(4):
            i = str(i)
            assert_input(response, name='comment_set-'+i+'-author', value='Author ' + i)
            assert_input(response, name='comment_set-'+i+'-content', value='Content ' + i)
            assert_input(response, name='comment_set-'+i+'-id', value='')
            assert_input(response, name='comment_set-'+i+'-post', value='')

        assert_management_form_inputs(response, total=4+extra, initial=0, max_num='')


    def test_clone_should_create_new_object_with_inlines_on_POST(self):
        response = self.app.get(self.post_with_comments_url, user='admin')
        response.form.submit()

        post1, post2 = Post.objects.filter(title=self.post_with_comments.title)

        assert 2 == post1.comment_set.count()
        assert 2 == post2.comment_set.count()


    def test_clone_should_ignore_initial_data_of_inline_form_if_delete_is_checked(self):
        response = self.app.get(self.post_with_comments_url, user='admin')
        response.form.set('comment_set-0-DELETE', 'on')  # delete first comment
        response.form.submit()

        cloned_post = Post.objects.latest('id')

        assert 1 == cloned_post.comment_set.count()


# asserts

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

def cssselect_input_or_textarea(response, name):
    field = response.lxml.cssselect('input[name={0}]'.format(name))
    if len(field) == 0:
        field = response.lxml.cssselect('textarea[name={0}]'.format(name))
    return field

def assert_management_form_inputs(response, total, initial, max_num):
    assert_input(response, name='comment_set-TOTAL_FORMS', value=total)
    assert_input(response, name='comment_set-INITIAL_FORMS', value=initial)
    assert_input(response, name='comment_set-MAX_NUM_FORMS', value=max_num)
