from os import urandom
from django import forms
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.postgres.fields import (ArrayField, JSONField,)
from django.db import models
from django.db.models.query import QuerySet
from django.shortcuts import HttpResponseRedirect
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.html import mark_safe

from simple_history.admin import SimpleHistoryAdmin
import nested_admin


from core import settings
from core.settings import (
    AWS_BUCKET,
    INVENTORY_EFD_ORGANIZATION_ID,
    INVENTORY_EFL_ORGANIZATION_ID,
    INVENTORY_EFN_ORGANIZATION_ID,
)

from integration.apps.aws import (create_presigned_url, )
from integration.inventory import (create_inventory_item, update_inventory_item, get_vendor_id, get_inventory_obj)
from integration.crm import search_query
from brand.models import (License, LicenseProfile,)
from fee_variable.utils import (get_tax_and_mcsp_fee,)
from .mixin import AdminApproveMixin
from ..models import (
    Inventory,
    CustomInventory,
    Documents,
)
from ..tasks import (create_approved_item_po, notify_inventory_item_approved_task)
from ..data import(INVENTORY_ITEM_CATEGORY_NAME_ID_MAP, )


def get_category_id(org_id, category_name):
    return INVENTORY_ITEM_CATEGORY_NAME_ID_MAP.get(org_id, {}).get(category_name, '')


class InlineDocumentsAdmin(GenericStackedInline):
    """
    Configuring field admin view for ProfileContact model.
    """
    extra = 0
    readonly_fields = ('doc_type', 'file',)
    fields = ('doc_type', 'file',)
    model = Documents
    can_delete = False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # inventory = get_inventory_obj(inventory_name='inventory_efd')
        # result = inventory.get_user()
        # if result.get('code') == 0:
        #     procurement_rep = [(o.get('email'), o.get('name')) for o in result.get('users', []) if o.get('status') in ['active', 'invited']]
        #     procurement_rep.insert(0, ('', '-------'))
        #     self.fields['procurement_rep'] = forms.ChoiceField(choices=procurement_rep, required=False)

    class Meta:
        model = CustomInventory
        fields = '__all__'


class CustomInventoryAdmin(AdminApproveMixin, admin.ModelAdmin):
    """
    OrganizationRoleAdmin
    """
    form = CustomInventoryForm
    list_display = (
        'cultivar_name',
        'category_name',
        'vendor_name',
        'grade_estimate',
        'quantity_available',
        'farm_ask_price',
        'status',
        'created_on',
        'updated_on',
    )
    readonly_fields = (
        'cultivar_name',
        'status',
        # 'vendor_name',
        'crm_vendor_id',
        # 'client_code',
        'procurement_rep',
        'zoho_item_id',
        'sku',
        'books_po_id',
        'po_number',
        'approved_by',
        'approved_on',
        'created_by',
        'created_on',
        'updated_on',
    )
    fieldsets = (
        ('BATCH & QUALITY INFORMATION', {
            'fields': (
                'cultivar',
                'cultivar_name',
                'category_name',
                'quantity_available',
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
                'vendor_name',
                'crm_vendor_id',
                'client_code',
                'procurement_rep',
                'zoho_item_id',
                'sku',
                'books_po_id',
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

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'cultivar':
                field.queryset = field.queryset.filter(status='approved')
        return field


    def generate_sku(self, obj, postfix):
        sku = []
        # if not settings.PRODUCTION:
        #     sku.append('test')
        #     sku.append('sku')
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
            except Exception :
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
            tax_and_mcsp_fee = get_tax_and_mcsp_fee(obj.vendor_name, request,)
            if tax_and_mcsp_fee:
                if not obj.client_code or not obj.procurement_rep or not obj.crm_vendor_id:
                    self.get_crm_data(request, obj)
                if obj.client_code:
                    data = {}
                    data['item_type'] = 'inventory'
                    data['cf_client_code'] = obj.client_code
                    data['unit'] = 'lb'

                    data['name'] = obj.cultivar.cultivar_name
                    data['cf_cultivar_name'] = obj.cultivar.cultivar_name
                    data['cf_strain_name'] = obj.cultivar.cultivar_name

                    if obj.cultivar.cultivar_type:
                        data['cf_cultivar_type'] = obj.cultivar.cultivar_type
                    if obj.category_name:
                        category_id = get_category_id(INVENTORY_EFD_ORGANIZATION_ID, obj.category_name)
                        if category_id:
                            data['category_name'] = obj.category_name
                            data['category_id'] = category_id

                    if obj.harvest_date:
                        data['cf_harvest_date'] = str(obj.harvest_date)  # not in inventor

                    if obj.batch_availability_date:
                        data['cf_date_available'] = str(obj.batch_availability_date)

                    if obj.grade_estimate:
                        data['cf_grade_seller'] = obj.grade_estimate

                    if obj.product_quality_notes:
                        data['cf_batch_quality_notes'] = obj.product_quality_notes

                    if obj.need_lab_testing_service is not None:
                        data['cf_lab_testing_services'] = 'Yes' if obj.need_lab_testing_service else 'No'

                    if obj.farm_ask_price:
                        data['cf_farm_price'] = str(int(obj.farm_ask_price))
                        data['cf_farm_price_2'] = obj.farm_ask_price
                        # data['purchase_rate'] = obj.farm_ask_price
                        data['rate'] = obj.farm_ask_price + sum(tax_and_mcsp_fee)

                    if obj.pricing_position:
                        data['cf_seller_position'] = obj.pricing_position
                    if obj.have_minimum_order_quantity:
                        data['cf_minimum_quantity'] = int(obj.minimum_order_quantity)

                    if obj.vendor_name:
                        data['cf_vendor_name'] = obj.vendor_name
                        # data['vendor_name'] = obj.vendor_name

                    if obj.payment_terms:
                        data['cf_payment_terms'] = obj.payment_terms

                    if obj.payment_method:
                        data['cf_payment_method'] = obj.payment_method

                    if obj.procurement_rep:
                        data['cf_procurement_rep'] = obj.procurement_rep

                    # data['initial_stock'] = int(obj.quantity_available)
                    data['product_type'] = 'goods'
                    data['cf_sample_in_house'] = 'Pending'
                    data['cf_status'] = 'In-Testing'
                    data['cf_cfi_published'] = False
                    data['account_id'] = 2155380000000448337 if settings.PRODUCTION else 2185756000001423419
                    # data['account_name'] = '3rd Party Flower Sales'
                    data['purchase_account_id'] = 2155380000000565567 if settings.PRODUCTION else 2185756000001031365
                    # data['purchase_account_name'] = 'Product Costs - Flower'
                    data['inventory_account_id'] = 2155380000000448361 if settings.PRODUCTION else 2185756000001423111
                    # data['inventory_account_name'] = 'Inventory - In the Field'
                    data['is_taxable'] = True

                    self._approve(request, obj, data,)

    def _approve(self, request, obj, data, sku_postfix=0):
        sku = self.generate_sku(obj, sku_postfix)
        data['sku'] = sku
        try:
            result = create_inventory_item(inventory_name='inventory_efd', record=data, params={})
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
                    obj.approved_by = {
                        'email': request.user.email,
                        'phone': request.user.phone.as_e164,
                        'name': request.user.get_full_name(),
                    }
                    obj.save()
                    self.message_user(request, 'This item is approved', level='success')
                    create_approved_item_po.apply_async((obj.id,), countdown=5)
                    notify_inventory_item_approved_task.delay(obj.id)
            elif result.get('code') == 1001 and 'SKU' in result.get('message', '') and sku in result.get('message', ''):
                self._approve(request, obj, data, sku_postfix=sku_postfix+1)
            else:
                self.message_user(request, 'Error while creating item in Zoho Inventory', level='error')
                print('Error while creating item in Zoho Inventory')
                print(result)
                print(data)

    def cultivar_name(self, obj):
            return obj.cultivar.cultivar_name

    # def test_action(self, request, queryset):
    #     pass
