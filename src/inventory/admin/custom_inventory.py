# from os import urandom
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
# from django.contrib.postgres.fields import (ArrayField, JSONField,)
# from django.core.exceptions import ValidationError
# from django.db import models
# from django.db.models.query import QuerySet
from django.utils import timezone
# from django.utils.encoding import force_str
from django.utils.html import mark_safe


from core import settings
from core.settings import (
    AWS_BUCKET,
)

from integration.apps.aws import (create_presigned_url, )
from integration.inventory import (
    get_inventory_obj,
    get_item_category_id,
    get_vendor_id,
)
from integration.crm import search_query
from fee_variable.utils import (get_item_mcsp_fee,)
from core.mixins.admin import (CustomButtonMixin,)
from utils import (get_approved_by, )
from ..models import (
    CustomInventory,
    Documents,
)
from ..tasks import (
    create_approved_item_po_task,
    notify_inventory_item_approved_task,
)
from ..utils import (
    get_item_tax,
)
from ..data import (CG, )
from .custom_inventory_helpers import (get_new_item_data,)



class InlineDocumentsAdmin(GenericStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    verbose_name = 'Document'
    verbose_name_plural = 'Documents'
    extra = 0
    readonly_fields = ('doc_type', 'file',)
    fields = ('doc_type', 'file',)
    model = Documents
    can_delete = False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(doc_type__in=('item_image', 'labtest'))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def file(self, obj):
        url = self.url(obj)
        if url and obj.doc_type == 'item_image':
            return mark_safe(
                '<div style="max-width: 500px;">'
                f'<a href="{url}" target="_blank">'
                f'<img src="{url}" style="width: 100%;height: auto;" alt="Image"/>'
                '</a></div>'
            )
        return mark_safe(f'<a href="{url}" target="_blank">{url}</a>')
    file.short_description = 'Uploaded File'
    file.allow_tags = True

    def url(self, obj):
        """
        Return s3 item image.
        """
        if obj.box_url:
            return obj.box_url
        try:
            url = create_presigned_url(AWS_BUCKET, obj.path)
            return url.get('response')
        except Exception:
            return None


class CustomInventoryForm(forms.ModelForm):
    # trim_used_verified = forms.BooleanField(label='Used Trim Verified', initial=False, required=False)


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     instance = kwargs.get('instance')
    #     if instance and instance.zoho_organization:
    #         if instance.zoho_organization == 'efd':
    #             marketplace_status_choices = (
    #                 ('Vegging', _('Vegging')),
    #                 ('Flowering', _('Flowering')),
    #                 ('Processing', _('Processing')),
    #                 ('In-Testing', _('In-Testing')),
    #                 ('Available', _('Available')),
    #             )
    #             self.fields['marketplace_status'] = forms.ChoiceField(choices=marketplace_status_choices, required=True)
    #         elif instance.zoho_organization == 'efl':
    #             marketplace_status_choices =(
    #                 ('Vegging', _('Vegging')),
    #                 ('Flowering', _('Flowering')),
    #                 ('Processing', _('Processing')),
    #                 ('In-Testing', _('In-Testing')),
    #                 ('Available', _('Available')),
    #             )
    #             self.fields['marketplace_status'] = forms.ChoiceField(choices=marketplace_status_choices, required=True)
    #             self.fields['harvest_date'].label='Manufacturing Date'
    #         elif instance.zoho_organization  == 'efn':
    #             marketplace_status_choices =(
    #                 ('Rooting', _('Rooting')),
    #                 ('Available', _('Available')),
    #             )
    #             self.fields['marketplace_status'] = forms.ChoiceField(choices=marketplace_status_choices, required=True)
    #             self.fields['harvest_date'].label='Clone Date'

    # def clean_category_name(val):
    #     return super().clean_category_name()

    def clean(self):
        cleaned_data = super().clean()
        cat = cleaned_data.get('category_name')
        if getattr(self, 'instance'):
            if self.instance.status == 'pending_for_approval':
                if cat and CG.get(cat, '') in ('Isolates', 'Concentrates', 'Terpenes'):
                    if not cleaned_data.get('trim_used'):
                        self.add_error('trim_used', "This value is required for current item category.")
                    if not cleaned_data.get('trim_used_verified'):
                        self.add_error('trim_used_verified', "Please check doc to verify used trim quantity and mark as verified.")
                        # raise ValidationError("Please check doc to verify used trim quantity and mark as verified.")
        return cleaned_data

    class Meta:
        model = CustomInventory
        fields = '__all__'


class CustomInventoryAdmin(CustomButtonMixin, admin.ModelAdmin):
    """
    Vendors Inventory Admin
    """
    form = CustomInventoryForm
    list_display = (
        'cultivar_name',
        'category_name',
        'vendor_name',
        'license_profile',
        'grade_estimate',
        'quantity_available',
        'farm_ask_price',
        'marketplace_status',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        'trim_used_doc',
        'status',
        'cultivar_name',
        # 'vendor_name',
        'crm_vendor_id',
        # 'client_code',
        'procurement_rep',
        'zoho_item_id',
        'sku',
        'po_id',
        'po_number',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    fieldsets = (
        (None, {
            'fields': (
                'zoho_organization',
            ),
        }),
        ('BATCH & QUALITY INFORMATION', {
            'fields': (
                'cultivar',
                # 'cultivar_name',
                'category_name',
                'marketplace_status',
                'quantity_available',
                ('trim_used', 'trim_used_doc'),
                'trim_used_verified',
                'harvest_date',
                'need_lab_testing_service',
                'batch_availability_date',
                'grade_estimate',
                'product_quality_notes',
        ),
        }),
        ('PRICING INFORMATION', {
            'fields': (
                'farm_ask_price',
                'pricing_position',
                # 'have_minimum_order_quantity',
                # 'minimum_order_quantity',
            ),
        }),
        ('SAMPLE LOGISTICS (PICKUP OR DROP OFF)', {
            'fields': (
                'transportation',
                'best_contact_Day_of_week',
                'best_contact_time_from',
                'best_contact_time_to',
            ),
        }),
        ('PAYMENT', {
            'fields': (
                'payment_terms',
                'payment_method',
            ),
        }),
        ('Extra Info', {
            'fields': (
                'status',
                'license_profile',
                'vendor_name',
                'crm_vendor_id',
                'client_code',
                'procurement_rep',
                'zoho_item_id',
                'sku',
                'po_id',
                'po_number',
                'approved_by',
                'approved_on',
                'created_by',
                'created_on',
                'updated_on',
            ),
        }),
    )
    inlines = [InlineDocumentsAdmin,]
    # actions = ['test_action', ]
    custom_buttons=('approve',)
    # custom_buttons_prop = {
    #     'approve': {
    #         'label': 'Approve',
    #         'color': '#ba2121',
    #     }
    # }

    def show_approve_button(self, request, obj,  add=False, change=False):
        return change and obj and obj.status == 'pending_for_approval'

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
            field.queryset = field.queryset.filter(status='approved')
        return field

    def has_change_permission(self, request, obj=None):
        if obj and obj.status == 'pending_for_approval':
            return True
        return False

    def generate_sku(self, obj, postfix):
        sku = []
        if not settings.PRODUCTION and obj.zoho_organization in ['efl', 'efn']:
            sku.append('test')
            sku.append('sku')
        sku.append(obj.client_code)
        sku.append(obj.cultivar.cultivar_name.replace(' ', '-'))

        if obj.harvest_date:
            sku.append(obj.harvest_date.strftime('%m-%d-%y'))

        if postfix:
            sku.append(str(postfix))

        # if not settings.PRODUCTION:
        #     sku.append(force_str(urandom(3).hex()))

        return '-'.join(sku)

    def get_crm_data(self, request, obj):
        found_code = False
        if obj.vendor_name:
            try:
                result = search_query('Vendors', obj.vendor_name, 'Vendor_Name')
            except Exception:
                self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')
            else:
                if result.get('status_code') == 200:
                    data_ls = result.get('response')
                    if data_ls and isinstance(data_ls, list):
                        for vendor in data_ls:
                            if vendor.get('Vendor_Name') == obj.vendor_name:
                                if not obj.crm_vendor_id:
                                    obj.crm_vendor_id = vendor.get('id', '')
                                if not obj.procurement_rep:
                                    p_rep = vendor.get('Owner', {}).get('email')
                                    if p_rep:
                                        obj.procurement_rep = p_rep
                                    p_rep_name = vendor.get('Owner', {}).get('name')
                                    if p_rep_name:
                                        obj.procurement_rep_name = p_rep_name
                                client_code = vendor.get('Client_Code')
                                if client_code:
                                    found_code = True
                                    obj.client_code = client_code
                                    return client_code

                if result.get('status_code') == 204 or not found_code:
                    try:
                        result = search_query('Accounts', obj.vendor_name, 'Account_Name')
                    except Exception:
                        self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')
                    else:
                        if result.get('status_code') == 200:
                            data_ls = result.get('response')
                            if data_ls and isinstance(data_ls, list):
                                for vendor in data_ls:
                                    if vendor.get('Account_Name') == obj.vendor_name:
                                        if not obj.procurement_rep:
                                            p_rep = vendor.get('Owner', {}).get('email')
                                            if p_rep:
                                                obj.procurement_rep = p_rep
                                            p_rep_name = vendor.get('Owner', {}).get('name')
                                            if p_rep_name:
                                                obj.procurement_rep_name = p_rep_name
                                        client_code = vendor.get('Client_Code')
                                        if client_code:
                                            obj.client_code = client_code
                                            return client_code
                                        else:
                                            self.message_user(request, f'client code not found for vendor \'{obj.vendor_name}\' in Zoho CRM', level='error')
                                self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                        elif result.get('status_code') == 204 or not found_code:
                            self.message_user(request, 'Vendor not found in Zoho CRM', level='error')
                else:
                    self.message_user(request, 'Error while fetching client code from Zoho CRM', level='error')

        return None

    def approve(self, request, obj):
        if obj.status == 'pending_for_approval':
            mcsp_fee = get_item_mcsp_fee(
                obj.vendor_name,
                license_profile=obj.license_profile,
                item_category_group=CG.get(obj.category_name),
                request=request,
            )
            if mcsp_fee:
                tax = get_item_tax(obj, request)
                if tax:
                    if not obj.client_code or not obj.procurement_rep or not obj.crm_vendor_id:
                        self.get_crm_data(request, obj)
                    if obj.client_code:
                        if obj.zoho_organization:
                            inv_obj = get_inventory_obj(inventory_name=f'inventory_{obj.zoho_organization}')
                            category_id = get_item_category_id(inv_obj.ORGANIZATION_ID, obj.category_name)
                            if category_id:
                                if obj.vendor_name:
                                    vendor_id = get_vendor_id(inv_obj, obj.vendor_name)
                                    if not vendor_id and obj.license_profile:
                                        vendor_id = get_vendor_id(inv_obj, obj.license_profile.license.legal_business_name)
                                    if vendor_id:
                                        data = get_new_item_data(obj, inv_obj, category_id, vendor_id, tax, mcsp_fee)
                                        self._approve(request, obj, inv_obj, data,)
                                    else:
                                        self.message_user(request, 'Vendor not found on zoho', level='error')
                                else:
                                    self.message_user(request, 'Vendor Name is not set', level='error')
                            else:
                                self.message_user(request, 'Invalid item category for selected Zoho inventory Organization', level='error')


    def _approve(self, request, obj, inv_obj, data, sku_postfix=0):
        sku = self.generate_sku(obj, sku_postfix)
        data['sku'] = sku
        try:
            result = inv_obj.create_item(data, params={})
        except Exception as exc:
            self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
            print('Error while creating item in Zoho Inventory')
            print(exc)
            print(data)
        else:
            if result.get('code') == 0:
                item_id = result.get('item', {}).get('item_id')
                if item_id:
                    obj.status = 'approved'
                    obj.zoho_item_id = item_id
                    obj.sku = sku
                    obj.approved_on = timezone.now()
                    obj.approved_by = get_approved_by(user=request.user)
                    obj.save()
                    self.message_user(request, 'This item is approved', level='success')
                    if obj.marketplace_status in ('In-Testing', 'Available'):
                        if settings.PRODUCTION or obj.zoho_organization in ['efd',]:
                            create_approved_item_po_task.delay(obj.id)
                        notify_inventory_item_approved_task.delay(obj.id)
                    else:
                        notify_inventory_item_approved_task.delay(obj.id, notify_logistics=False)

            elif result.get('code') == 1001 and 'SKU' in result.get('message', '') and sku in result.get('message', ''):
                self._approve(request, obj, inv_obj, data, sku_postfix=sku_postfix+1)
            else:
                msg = result.get('message')
                if msg:
                    self.message_user(request, f'Error while creating item in Zoho Inventory:  {msg}', level='error')
                else:
                    self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                print('Error while creating item in Zoho Inventory')
                print(result)
                print(data)

    def cultivar_name(self, obj):
        return obj.cultivar.cultivar_name

    # def test_action(self, request, queryset):
    #     pass


    def get_doc_url(self, obj, doc_type):
        """
        Return s3 license url.
        """
        try:
            document_obj = Documents.objects.filter(object_id=obj.id, doc_type=doc_type).latest('created_on')
            if document_obj.box_url:
                return document_obj.box_url
            else:
                path = document_obj.path
                url = create_presigned_url(AWS_BUCKET, path)
                if url.get('response'):
                    return url.get('response')
        except Exception:
            return None

    def trim_used_doc(self, obj):
        url = self.get_doc_url(obj, doc_type='trim_used_doc')
        if url:
            return mark_safe(f'<a href="{url}" target="_blank">{url}</a>')
    trim_used_doc.short_description = 'Document'
    trim_used_doc.allow_tags = True
