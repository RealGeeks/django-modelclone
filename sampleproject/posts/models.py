from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=256)
    content = models.TextField(blank=True)
    tags = models.ManyToManyField('Tag', blank=True)

    def __unicode__(self):
        return u'Post: {0}'.format(self.title)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.CharField(max_length=256)
    content = models.TextField()

    def __unicode__(self):
        return u'Comment on {0} by {1}'.format(self.post, self.author)


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name


class Multimedia(models.Model):
    title = models.CharField(max_length=256)
    image = models.ImageField(upload_to='images', blank=True)
    document = models.FileField(upload_to='documents', blank=True)

    def __unicode__(self):
        msg = [self.title]
        if self.image:
            msg.append('Image: ' + unicode(self.image))
        if self.document:
            msg.append('Document: ' + unicode(self.document))
        return u' '.join(msg)
