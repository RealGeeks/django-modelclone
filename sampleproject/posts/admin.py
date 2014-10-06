from django.contrib import admin

from modelclone import ClonableModelAdmin

from .models import Post, Comment, Tag, Multimedia


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 2

class PostAdmin(ClonableModelAdmin):
    inlines = CommentInline,
    clone_verbose_name = 'Clone it!'

    list_display = '__unicode__', 'clone_link'

    def tweak_cloned_fields(self, fields):
        fields['title'] = u"%s (duplicate)" % fields['title']
        return fields

    def tweak_cloned_inline_fields(self, fkname, fields_list):
        # This is a silly override just to demonstrate the feature and to be able to test it.
        if fkname == 'comment_set':
            fields_list = [comment for comment in fields_list if comment['author'] != 'do-not-clone']
        return fields_list

class MultimediaAdmin(ClonableModelAdmin):
    pass

admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(Multimedia, MultimediaAdmin)
