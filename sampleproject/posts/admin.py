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

class MultimediaAdmin(ClonableModelAdmin):
    pass

admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(Multimedia, MultimediaAdmin)
