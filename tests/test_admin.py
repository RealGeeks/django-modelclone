from django.contrib.auth.models import User
from django_webtest import WebTest

from sampleproject.posts.models import Post, Comment


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


    # clone object with inlines

    def test_clone_should_pre_fill_all_form_fields_including_inlines_on_GET(self):
        response = self.app.get(self.post_with_comments_url, user='admin')

        # comment 1
        assert_input(response, name='comment_set-0-author', value='Bob')
        assert_input(response, name='comment_set-0-content', value='Thanks! It really helped')
        assert_input(response, name='comment_set-0-id', value='')
        assert_input(response, name='comment_set-0-post', value='')

        # comment 2
        assert_input(response, name='comment_set-1-author', value='Alice')
        assert_input(response, name='comment_set-1-content', value='Oh, really?!')
        assert_input(response, name='comment_set-1-id', value='')
        assert_input(response, name='comment_set-1-post', value='')

        # management form data
        assert_management_form_inputs(response, total=3, initial=0, max_num='')


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



# asserts

def assert_input(response, name, value=None):
    '''
    Verify if the input with ``name`` exists in ``response``

    If value is not None, assert the input value is ``value``
    '''
    field = response.lxml.cssselect('input[name={0}]'.format(name))
    if len(field) == 0:
        field = response.lxml.cssselect('textarea[name={0}]'.format(name))

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



def assert_management_form_inputs(response, total, initial, max_num):
    assert_input(response, name='comment_set-TOTAL_FORMS', value=total)
    assert_input(response, name='comment_set-INITIAL_FORMS', value=initial)
    assert_input(response, name='comment_set-MAX_NUM_FORMS', value=max_num)
