from django.contrib import admin

from modelclone import ClonableModelAdmin

from .models import Post, Comment


class CommentInline(admin.StackedInline):
    model = Comment

class PostAdmin(ClonableModelAdmin):
    inlines = CommentInline,


admin.site.register(Post, PostAdmin)
