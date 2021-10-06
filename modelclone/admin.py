from django import VERSION
from django.contrib.admin import ModelAdmin, helpers
try:
    from django.contrib.admin.utils import unquote
except ImportError:
    # django < 1.7
    from django.contrib.admin.util import unquote
from django.urls import re_path as url
from django.utils.encoding import force_text
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as lazy
from django.utils.html import escape
from django.forms.models import model_to_dict
from django.forms.formsets import all_valid
if VERSION[0] < 2:
    from django.core.urlresolvers import reverse
else:
    from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models.fields.files import FieldFile, FileField


__all__ = 'ClonableModelAdmin',

class ClonableModelAdmin(ModelAdmin):

    clone_verbose_name = lazy('Duplicate')
    change_form_template = 'modelclone/change_form.html'

    def clone_link(self, clonable_model):
        '''
        Method to be used on `list_display`, renders a link to clone model
        '''
        _url = reverse(
            'admin:{0}_{1}_clone'.format(
                clonable_model._meta.app_label,
                getattr(clonable_model._meta, 'module_name', getattr(clonable_model._meta, 'model_name', ''))),
            args=(clonable_model._get_pk_val(),),
            current_app=self.admin_site.name
        )
        return '<a href="{0}">{1}</a>'.format(_url, self.clone_verbose_name)

    clone_link.short_description = clone_verbose_name  # not overridable by subclass
    clone_link.allow_tags = True

    def get_urls(self):
        url_name = '{0}_{1}_clone'.format(
            self.model._meta.app_label,
            getattr(self.model._meta, 'module_name', getattr(self.model._meta, 'model_name', '')))

        if VERSION[0] == 1 and VERSION[1] < 9:
            from django.conf.urls import patterns
            new_urlpatterns = patterns('',
                url(r'^(.+)/clone/$',
                    self.admin_site.admin_view(self.clone_view),
                    name=url_name)
                )
        else:
            new_urlpatterns = [
                url(r'^(.+)/change/clone/$',
                    self.admin_site.admin_view(self.clone_view),
                    name=url_name)
            ]

        original_urlpatterns = super(ClonableModelAdmin, self).get_urls()

        return new_urlpatterns + original_urlpatterns

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'clone_verbose_name': self.clone_verbose_name,
            'include_clone_link': True,
        })
        return super(ClonableModelAdmin, self).change_view(request, object_id, form_url, extra_context)

    def clone_view(self, request, object_id, form_url='', extra_context=None):
        opts = self.model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        original_obj = self.get_object(request, unquote(object_id))

        if original_obj is None:
            raise Http404(_('{name} object with primary key {key} does not exist.'.format(
                name=force_text(opts.verbose_name),
                key=repr(escape(object_id))
            )))

        ModelForm = self.get_form(request)
        formsets = []

        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                new_object = self.model()
                form_validated = False

            prefixes = {}
            for FormSet, inline in self.get_formsets_with_inlines(request):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1 or not prefix:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])

                request_files = request.FILES
                filter_params = {'%s__pk' % original_obj.__class__.__name__.lower(): original_obj.pk}
                inlined_objs = inline.model.objects.filter(**filter_params)
                for n, inlined_obj in enumerate(inlined_objs.all()):
                    for field in inlined_obj._meta.fields:
                        if isinstance(field, FileField) and field not in request_files:
                            value = field.value_from_object(inlined_obj)
                            file_field_name = '{}-{}-{}'.format(prefix, n, field.name)
                            request_files.setdefault(file_field_name, value)

                formset = FormSet(data=request.POST, files=request_files,
                                  instance=new_object,
                                  save_as_new="_saveasnew" in request.POST,   # ????
                                  prefix=prefix)
                formsets.append(formset)

            if all_valid(formsets) and form_validated:

                # if original model has any file field, save new model
                # with same paths to these files
                for name in vars(original_obj):
                    field = getattr(original_obj, name)
                    if isinstance(field, FieldFile) and name not in request.FILES:
                        setattr(new_object, name, field)

                self.save_model(request, new_object, form, False)
                self.save_related(request, form, formsets, False)
                try:
                    self.log_addition(request, new_object)
                except TypeError:
                    # In Django 1.9 we need one more param
                    self.log_addition(request, new_object, "Cloned object")

                return self.response_add(request, new_object, None)

        else:
            initial = model_to_dict(original_obj)
            initial = self.tweak_cloned_fields(initial)
            form = ModelForm(initial=initial)

            prefixes = {}
            for FormSet, inline in self.get_formsets_with_inlines(request):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1 or not prefix:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                initial = []

                queryset = inline.get_queryset(request).filter(
                    **{FormSet.fk.name: original_obj})
                for obj in queryset:
                    initial.append(model_to_dict(obj, exclude=[obj._meta.pk.name,
                                                               FormSet.fk.name]))
                initial = self.tweak_cloned_inline_fields(prefix, initial)
                formset = FormSet(prefix=prefix, initial=initial)
                # Since there is no way to customize the `extra` in the constructor,
                # construct the forms again...
                # most of this view is a hack, but this is the ugliest one
                formset.extra = len(initial) + formset.extra
                # _construct_forms() was removed on django 1.6
                # see https://github.com/django/django/commit/ef79582e8630cb3c119caed52130c9671188addd
                if hasattr(formset, '_construct_forms'):
                    formset._construct_forms()
                formsets.append(formset)

        admin_form = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request)),
            self.get_prepopulated_fields(request),
            self.get_readonly_fields(request),
            model_admin=self
        )
        media = self.media + admin_form.media

        inline_admin_formsets = []
        for inline, formset in zip(self.get_inline_instances(request), formsets):
            fieldsets = list(inline.get_fieldsets(request, original_obj))
            readonly = list(inline.get_readonly_fields(request, original_obj))
            prepopulated = dict(inline.get_prepopulated_fields(request, original_obj))
            inline_admin_formset = InlineAdminFormSetFakeOriginal(inline, formset,
                fieldsets, prepopulated, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media


        title = u'{0} {1}'.format(self.clone_verbose_name, opts.verbose_name)

        context = {
            'title': title,
            'original': title,
            'adminform': admin_form,
            'is_popup': "_popup" in getattr(request, 'REQUEST', request.GET),
            'show_delete': False,
            'media': media,
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})

        return self.render_change_form(request,
            context,
            form_url=form_url,
            change=False
        )

    def tweak_cloned_fields(self, fields):
        """Override this method to tweak a cloned object before displaying its form.

        ``fields`` is a dictionary containing the cloned object's field data (the result of
        ``model_to_dict()``).

        It does *not* contain inline fields. To tweak inline fields, override
        ``tweak_cloned_inline_fields()``.

        This method returns the modified ``fields``.
        """
        return fields

    def tweak_cloned_inline_fields(self, related_name, fields_list):
        """Override this method to tweak a cloned inline before displaying its form.

        ``related_name`` is the name of the relation being inlined. Note that if you've inline the
        same relation more than once, ``related_name`` will have a numerical suffix, for example,
        ``comment_set-2``.

        ``fields_list`` is a list of dictionaries containing the inline field data (the result of
        ``model_to_dict()`` for each inlined row).

        This method returns the modified ``fields_list``.
        """
        return fields_list

class InlineAdminFormSetFakeOriginal(helpers.InlineAdminFormSet):

    def __iter__(self):
        # the template requires the AdminInlineForm to have an `original`
        # attribute, which is the model instance, in order to display the
        # 'Delete' checkbox
        # we don't have `original` because we are just providing initial
        # data to the form, so we attach a "fake original" (something that
        # evaluates to True) to fool the template and make is display
        # the 'Delete' checkbox
        # needless to say this is a terrible hack and will break in future
        # django versions :)
        for inline_form in super(InlineAdminFormSetFakeOriginal, self).__iter__():
            if inline_form.form.initial:
                inline_form.original = True
            yield inline_form
