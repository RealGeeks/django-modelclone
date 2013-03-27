from django.contrib.admin import ModelAdmin, helpers
from django.contrib.admin.util import unquote
from django.conf.urls import patterns, url
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.forms.models import _get_foreign_key, model_to_dict
from django.forms.formsets import all_valid

__all__ = 'ClonableModelAdmin',

class ClonableModelAdmin(ModelAdmin):

    clone_verbose_name = _('Duplicate')
    change_form_template = 'modelclone/change_form.html'

    def get_urls(self):
        new_urlpatterns = patterns('',
            url(r'^(.+)/clone/',
                self.admin_site.admin_view(self.clone_view)),
        )
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

        original_obj = self.get_object(request, unquote(object_id))

        ModelForm = self.get_form(request)
        formsets = []

        # NOTE: Django 1.5 has a secong argument on get_inline_instances()
        inline_instances = self.get_inline_instances(request)

        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                new_object = self.model()
                form_validated = False

            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request), inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1 or not prefix:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(data=request.POST, files=request.FILES,
                                  instance=new_object,
                                  save_as_new="_saveasnew" in request.POST,   # ????
                                  prefix=prefix)
                formsets.append(formset)

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, False)
                self.save_related(request, form, formsets, False)
                self.log_addition(request, new_object)
                return self.response_add(request, new_object)

        else:
            initial = model_to_dict(original_obj)
            form = ModelForm(initial=initial)

            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request), inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1 or not prefix:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                initial = []
                queryset = inline.queryset(request).filter(
                    **{FormSet.fk.name: original_obj})
                for obj in queryset:
                    initial.append(model_to_dict(obj, exclude=[obj._meta.pk.name,
                                                               FormSet.fk.name]))
                formset = FormSet(prefix=prefix, initial=initial)
                # since there is no way to customize the `extra` in the constructor,
                # construct the forms again...
                # most of this view is a hack, but this is the ugliest one
                formset.extra = len(initial) + formset.extra
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
        for inline, formset in zip(inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, original_obj))
            readonly = list(inline.get_readonly_fields(request, original_obj))
            prepopulated = dict(inline.get_prepopulated_fields(request, original_obj))
            inline_admin_formset = InlineAdminFormSetFakeOriginal(inline, formset,
                fieldsets, prepopulated, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media


        context = {
            'title': self.clone_verbose_name,
            'original': self.clone_verbose_name,
            'adminform': admin_form,
            'is_popup': "_popup" in request.REQUEST,
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
            change=True
        )

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
