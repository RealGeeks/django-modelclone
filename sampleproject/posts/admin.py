from django.contrib import admin

from modelclone import ClonableModelAdmin

from .models import Post, Comment


class CommentInline(admin.StackedInline):
    model = Comment
    extra = 2

class PostAdmin(ClonableModelAdmin):
    inlines = CommentInline,
    clone_verbose_name = 'Clone it!'


admin.site.register(Post, PostAdmin)
