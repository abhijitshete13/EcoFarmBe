import sys
import traceback
import ast
import json
from io import BytesIO
import hashlib
from datetime import (datetime, timedelta, )
from urllib.parse import (unquote, )
from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER,
    LICENSE_PARENT_FOLDER_ID,
    TEMP_LICENSE_FOLDER,
    AWS_BUCKET)
from django.conf import settings
from user.models import (User, )
from cultivar.models import (Cultivar, )
from labtest.models import (LabTest, )
from .crm_format import (CRM_FORMAT, VENDOR_TYPES,
                         VENDOR_LICENSE_TYPES, ACCOUNT_LICENSE_TYPES,
                         ACCOUNT_TYPES)
from .box import (get_shared_link, move_file,
                  create_folder, upload_file_stream)
from core.celery import app
from .utils import (get_vendor_contacts, get_account_category,
                    get_cultivars_date, get_layout, get_overview_field,)
from core.mailer import mail, mail_send
from brand.models import (Brand, License, LicenseProfile, Organization, ProgramOverview, NurseryOverview)
from integration.models import (Integration,)
from integration.apps.aws import (get_boto_client, )
from inventory.models import (Documents, )
from slacker import Slacker
slack = Slacker(settings.SLACK_TOKEN)

def get_crm_obj():
    """
    Return ZCRM object.
    """
    try:
        oauth = Integration.objects.get(name='crm')
        access_token = oauth.access_token
        access_expiry = oauth.access_expiry
    except Integration.DoesNotExist:
        access_expiry = access_token = None
    return CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER,
        access_token,
        access_expiry)

def get_picklist(module, field_name):
    """
    Return picklist for field.
    """
    picklist_types = ('picklist', 'multiselectpicklist', 'pick_list_values', )
    crm_obj = get_crm_obj()
    module = crm_obj.get_module(module)
    if module.get('response'):
        module = module['response']
        fields = module.get_all_fields().response_json['fields']
        for field in fields:
            if field['field_label'] == field_name and field['data_type'] in picklist_types:
                return field['pick_list_values']
    return list()

def get_format_dict(module):
    """
    Return Contact-CRM fields dictionary.
    """
    return CRM_FORMAT[module]

def get_vendor_types(vendor_type, reverse=False):
    """
    Return Zoho CRM vendor type
    """
    response = list()
    if reverse:
        for vendor in vendor_type:
            for k,v in VENDOR_TYPES.items():
                if v == vendor:
                    response.append(k)
    else:
        for vendor in vendor_type:
            type_ = VENDOR_TYPES.get(vendor)
            if type_:
                response.append(type_)
    return response

def get_dict(cd, i):
        user = dict()
        for k,v in cd.items():
            user[k] = i.get(v)
        user = create_records('Contacts', [user])
        if user['status_code'] in (201, 202):
            return user['response']['data'][0]['details']['id']

def get_users(user_type='ActiveUsers', email=None, page=1, per_page=200):
    """
    Get users from zoho CRM.
    """
    crm_obj = get_crm_obj()
    response = crm_obj.get_users(user_type, page=page, per_page=per_page)
    if response.get('status_code') != 200:
        return response
    if email:
        for i in response.get('response'):
            if i['email'] == email:
                return i
        return []
    return response

def get_user(user_id):
    """
    Get user from zoho CRM.
    """
    crm_obj = get_crm_obj()
    return crm_obj.get_user(user_id)

def create_employees(key, value, obj, crm_obj):
    """
    Create contacts in Zoho CRM.
    """
    user = None
    d = obj.get(value)
    cd = {
        'last_name': 'employee_name',
        'email': 'employee_email',
        'phone': 'phone',
    }
    try:
        for i in d:
            if 'Farm Manager' in i['roles'] and key == 'Contact_1':
                user = get_dict(cd, i)
            elif 'Logistics' in i['roles'] and key == 'Contact_2':
                user = get_dict(cd, i)
            elif 'Sales/Inventory' in i['roles'] and key == 'Contact_3':
                user = get_dict(cd, i)
            elif 'License Owner' in i['roles'] and key == 'Owner1':
                user = get_dict(cd, i)
        return user
    except IndexError:
        return []
    except TypeError:
        return []

def parse_fields(module, key, value, obj, crm_obj, **kwargs):
    """
    Parse fields
    """
    def create_or_get_user(last_name, email):
        data = {}
        data['last_name'] = last_name
        data['email'] = email
        user = create_records('Contacts', [data])
        if user['status_code'] in (201, 202):
            return user['response']['data'][0]['details']['id']

    def get_employees(id):
        data = get_record('Contacts', id)
        if data.get('status_code') == 200:
            return data.get('response').get(id)
        return {}

    def get_contact_from_crm(obj, id, is_buyer=False, is_seller=False):
        if is_buyer:
            data = search_query('Accounts_X_Contacts', id, 'Accounts')
        elif is_seller:
            data = search_query('Vendors_X_Contacts', id, 'Vendor')
        return data.get('response')

    cultivator_starts_with = (
        "co.",
        "fo.",
        "cr.",
    )
    if value.startswith('county') or value.startswith('appellation'):
        return obj.get(value).split(',')
    if value.startswith('County2') or value.startswith('Appellations'):
        if isinstance(obj.get(value), list):
            return ','.join(obj.get(value))
        return obj.get(value)
    if value.startswith('ethics_and_certification'):
        if isinstance(obj.get(value), list) and len(obj.get(value)) > 0:
            return obj.get(value)
        return []
    if value.startswith('program_details'):
        d = obj.get('program_details')
        if d and len(d) > 0:
            return d.get('program_name')
    if value.startswith('employees'):
        return create_employees(key, value, obj, crm_obj)
    if value == 'brand_category':
        return get_vendor_types(obj.get(value))
    if value.startswith('Contact'):
        return get_vendor_contacts(key, value, obj, crm_obj)
    if value.startswith('layout'):
        layout_name = obj.get('Layout_Name')
        return get_layout(module, layout_name)
    if value.startswith('account_category'):
        return get_account_category(key, value, obj, crm_obj)
    if value.startswith('logistic_manager_email'):
        if obj.get('logistic_manager_name'):
            return create_or_get_user(obj.get('logistic_manager_name'), obj.get(value))
    if value.startswith('Cultivars'):
        if obj.get(value):
            return obj.get(value).split(', ')
        return []
    list_fields = (
        'transportation',
        'cultivation_type',
        'vendor_type',
        'type_of_nutrients'
        )
    if value.startswith(list_fields):
        if isinstance(obj.get(value), list):
            return obj.get(value)
        return []
    boolean_conversion_list = ('issues_with_failed_labtest', 'cr.process_on_site', 'transportation')
    string_conversion_list = ('featured_on_our_site',)
    if value.startswith(boolean_conversion_list):
        return 'Yes' if obj.get(value) in [True, 'true', 'True'] else 'No'
    elif value.startswith(string_conversion_list):
        return True if obj.get(value) in ['true', 'True'] else False
    elif value.startswith(cultivator_starts_with):
        return get_overview_field(key, value, obj, crm_obj)
    if value in ('full_season', 'autoflower'):
        return "yes" if obj.get(value) else "No"
    if value.startswith(('billing_address', 'mailing_address')):
        v = value.split('.')
        if len(v) == 2 and obj.get(v[0]):
            return obj.get(v[0]).get(v[1])
    if value.startswith('cultivars'):
        cultivars = list()
        dictionary = obj.get('cr.overview')
        if dictionary:
            for i in dictionary:
                for j in i['cultivars']:
                    cultivars.extend(j['cultivar_names'])
        return list(set(cultivars))
    if value.startswith('contact_from_crm'):
        result = list()
        vendor_id = kwargs.get('vendor_id')
        account_id = kwargs.get('account_id')
        if vendor_id:
            data = get_contact_from_crm(obj, vendor_id, is_seller=True)
        elif account_id:
            data = get_contact_from_crm(obj, account_id, is_buyer=True)
        if data:
            for i in data:
                if vendor_id:
                    contact = get_employees(i['Contact']['id'])
                elif account_id:
                    contact = get_employees(i['Contacts']['id'])
                contact.update(i)
                result.append(contact)
            return result
        return []
    if value.startswith('Created_By'):
        return value
    
def get_record(module, record_id, full=False):
    """
    Get record.
    """
    crm_obj = get_crm_obj()
    if full:
        return crm_obj.get_full_record(module, record_id)
    return crm_obj.get_record(module, record_id)

def create_records(module, records, is_return_orginal_data=False):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    if isinstance(records, dict):
        records = [records]
    for record in records:
        record_dict = dict()
        crm_dict = get_format_dict(module)
        for k,v in crm_dict.items():
            if v.endswith('_parse'):
                v = v.split('_parse')[0]
                v = parse_fields(module, k, v, record, crm_obj)
                record_dict[k] = v
            else:
                v = record.get(v)
                record_dict[k] = v
        request.append(record_dict)
    response = crm_obj.insert_records(module, request, is_return_orginal_data)
    return response

def update_records(module, records, is_return_orginal_data=False):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    if isinstance(records, dict):
        records = [records]
    for record in records:
        record_dict = dict()
        crm_dict = get_format_dict(module)
        for k,v in crm_dict.items():
            if v.endswith('_parse'):
                v = v.split('_parse')[0]
                v = parse_fields(module, k, v, record, crm_obj)
            else:
                v = record.get(v)
            if v and ((v is not None) or len(v)>0):
                record_dict[k] = v
        request.append(record_dict)
    response = crm_obj.update_records(module, request, is_return_orginal_data)
    return response

def update_in_crm(module, record_id):
    """
    Update record in zoho crm.
    """
    try:
        if module == 'Licenses':
            request = License.objects.get(id=record_id)
            request = request.__dict__
        elif module in ['Vendors', 'Accounts']:
            lp_obj = LicenseProfile.objects.get(id=record_id)
            request = lp_obj.__dict__
            if module == 'Vendors':
                if lp_obj.license.profile_category == 'nursery':
                    request['Layout_Name'] = 'vendor_cannabis_nursery'
                else:
                    request['Layout_Name'] = 'vendor_cannabis'

        elif module == 'Orgs':
            request = Organization.objects.get(id=record_id)
            request = request.__dict__
        elif module == 'Brands':
            request = Brand.objects.get(id=record_id)
            request = request.__dict__
    except Exception as exc:
        print(exc)
        return {'error': 'Record not in database'}
    if request.get('zoho_crm_id'):
        request['id'] = request.get('zoho_crm_id')
        return update_records(module, request)
    return {'error': 'Record not in CRM'}

def delete_record(module, record_id):
    """
    Delete record from module.
    """
    crm_obj = get_crm_obj()
    response = crm_obj.delete_record(module, record_id)
    return response

def disassociate_brand(brand_name, vendor_name):
    """
    Disassociate brand from license.
    """
    response = search_query('Brands_X_Vendors', vendor_name, 'Vendor')
    if response.get('status_code') != 200:
        response = search_query('Brands_X_Accounts', vendor_name, 'Account')
    if response.get('status_code') == 200:
        for record in response.get('response'):
            if (record.get('Vendor') and record.get('Vendor').get('name') == vendor_name and
                record.get('Brand').get('name') == brand_name):
                return delete_record('Brands_X_Vendors', record.get('id'))
            elif (record.get('Account') and record.get('Account').get('name') == vendor_name and
                record.get('Brand').get('name') == brand_name):
                return delete_record('Brands_X_Accounts', record.get('id'))
    return response

def get_program_selection(program):
    """
    Return program selection.
    """
    PROGRAM_SELECTION = {
        'spot': 'Spot Market',
        'silver': 'IFP - Silver - Right of First Refusal',
        'gold': 'IFP - Gold - Exclusivity'
    }
    if "spot" in program:
        return PROGRAM_SELECTION['spot']
    elif "silver" in program:
        return PROGRAM_SELECTION['silver']
    elif "gold" in program:
        return PROGRAM_SELECTION['gold']
    else:
        return None

def update_vendor_tier(module, record):
    if record.get('program_selection'):
        crm_obj = get_crm_obj()
        request = dict()
        request['id'] = record.get('id')
        request['Program_Selection'] = get_program_selection(record.get('program_selection').lower())
        layout_name = record.get('Layout_Name')
        request['Layout'] = get_layout(module, layout_name)
        response = crm_obj.update_records(module, [request])
        return response
    return {'code': 1, 'status': 'Program selection not specified.'}

def search_query(module, query, criteria, case_insensitive=False, is_license=False):
    crm_obj = CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)
    if case_insensitive:
        return crm_obj.isearch_record(module, query, criteria)
    if is_license:
        return crm_obj.search_license(module, query, criteria)
    return crm_obj.search_record(module, query, criteria)

def insert_users():
    """
    Insert Users in Zoho CRM.
    """
    records = User.objects.filter(is_updated_in_crm=False, existing_member=False)
    if not records:
        return {'status': 'QuerySet empty. No records to push.'}
    response = create_records('Contacts', records.values())
    if response['status_code'] == 201:
        response = response['response']['data']
        for idx, record in enumerate(records):
            record.zoho_contact_id = response[idx]['details']['id']
            record.is_updated_in_crm = True
            record.save()
        return response
    else:
        return response

def get_licenses(license_field):
    """
    Get license from Zoho CRM.
    """
    licenses = search_query('Licenses', license_field, 'Legal_Business_Name')
    if licenses['status_code'] == 200:
        return licenses['response']

def is_user_existing(license_number):
    """
    Check if user is existing or not.
    """
    licenses = search_query('Licenses', license_number, 'Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        for license_dict in licenses.get('response'):
            vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
            if vendor['status_code'] != 200:
                vendor_id = get_vendors_from_licenses('Vendor_Name_Lookup', license_dict)
            else:
                vendor = vendor['response'][0]['Licenses_Module']
                vendor_id = vendor['id']
            if not vendor_id:
                account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
                if account['status_code'] != 200:
                    account_id = get_vendors_from_licenses('Account_Name_Lookup', license_dict)
                else:
                    account = account['response'][0]['Licenses_Module']
                    account_id = account['id']
                if not account_id:
                    return False, None
                else:
                    return True, 'Buyer'
            else:
                return True, 'Seller'
    return None

def insert_record(record=None, is_update=False, id=None, is_single_user=False):
    """
    Insert record to Zoho CRM.
    """
    if id and is_single_user:
        licenses = [License.objects.select_related().get(id=id).__dict__]
    else:
        licenses = [record.__dict__]
    final_list = dict()
    for i in licenses:
        try:
            final_dict = dict()
            d = dict()
            l = list()
            d.update(i)
            license_db_id= i['id']
            d.update({'license_db_id': license_db_id})
            license_db = License.objects.select_related().get(id=license_db_id)
            licenses = get_licenses(i['legal_business_name'])
            d.update(license_db.license_profile.__dict__)
            try:
                d.update(license_db.profile_contact.profile_contact_details)
            except Exception:
                pass
            vendor_id = license_db.license_profile.__dict__['id']
            try:
                for k, v in license_db.cultivation_overview.__dict__.items():
                    d.update({'co.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db.financial_overview.__dict__.items():
                    d.update({'fo.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db.crop_overview.__dict__.items():
                    d.update({'cr.' + k:v})
            except Exception:
                pass
            try:
                for k, v in license_db.nursery_overview.__dict__.items():
                    d.update({'no.' + k:v})
            except Exception:
                pass
            try:
                d.update(license_db.program_overview.__dict__)
            except Exception:
                pass
            d.update({'id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
            l.append(d['id'])
            d.update({'licenses': l})
            if id and is_single_user and is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
            # farm_name = license_db.license_profile.__dict__['name']
            farm_name = i['legal_business_name']
            if d['is_buyer'] == True:
                continue
            response = update_license(dba=farm_name, license=d)
            final_dict['license'] = response
            if response['status_code'] == 200:
                    record_response = response['response']['data']
                    try:
                        record_obj = License.objects.get(id=license_db_id)
                        record_obj.zoho_crm_id = record_response[0]['details']['id']
                        record_obj.is_updated_in_crm = True
                        record_obj.save()
                    except KeyError as exc:
                        print(exc)
                        pass
            if i['profile_category'] == 'nursery':
                d['Layout_Name'] = 'vendor_cannabis_nursery'
            else:
                d['Layout_Name'] = 'vendor_cannabis'
            if is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
                if d['id']:
                    r = search_query('Vendors', d['name'], 'Vendor_Name')
                    if r.get('status_code') == 200:
                        d['id'] = r.get('response')[0]['id']
                if d['id']:
                    result = update_records('Vendors', d, True)
                else:
                    result = create_records('Vendors', d, True)
            else:
                result = search_query('Vendors', d['name'], 'Vendor_Name')
                if result.get('status_code') != 200:
                    result = create_records('Vendors', d, True)
                else:
                    d['id'] = result.get('response')[0]['id']
                    result = update_records('Vendors', d, True)
            final_dict['vendor'] = result
            if response['status_code'] == 200 and result['status_code'] in [200, 201]:
                record_response = result['response']['response']['data']
                try:
                    record_obj = LicenseProfile.objects.get(id=vendor_id)
                    record_obj.zoho_crm_id = record_response[0]['details']['id']
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)
                    pass
                if (result['response']['orignal_data'][0].get('Licenses_List')):
                    data = dict()
                    data['Licenses_Module'] = record_response[0]['details']['id']
                    for license in result['response']['orignal_data'][0]['Licenses_List']:
                        data['Licenses'] = license
                        if is_update:
                            r = update_records('Vendors_X_Licenses', [data])
                            if r.get('status_code') == 202:
                                r = create_records('Vendors_X_Licenses', [data])
                        else:
                            r = create_records('Vendors_X_Licenses', [data])
                if result['response']['orignal_data'][0].get('Cultivars_List'):
                    data = dict()
                    l = list()
                    data['Cultivar_Associations'] = record_response[0]['details']['id']
                    for j in result['response']['orignal_data'][0]['Cultivars_List']:
                            r = search_query('Cultivars', j, 'Name')
                            if r['status_code'] == 200:
                                data['Cultivars'] = r['response'][0]['id']
                                r = create_records('Vendors_X_Cultivars', [data])
                request = list()
                contact_dict = {
                    'Owner1': 'Owner',
                    'Contact_1': 'Cultivation Manager',
                    'Contact_2': 'Logistics Manager',
                    'Contact_3': 'Sales Manager'}
                for contact in ['Owner1', 'Contact_1', 'Contact_2', 'Contact_3']:
                    data = dict()
                    user_id = result['response']['orignal_data'][0].get(contact)
                    if user_id:
                        if len(request) == 0:
                            data['Contact'] = user_id
                            data['Contact_Company_Role'] = [contact_dict[contact]]
                            data['Vendor'] = record_response[0]['details']['id']
                            request.append(data)
                        else:
                            inserted = False
                            for j in request:
                                if j.get('Contact') == user_id:
                                    j['Contact_Company_Role'].append(contact_dict[contact])
                                    inserted = True
                            if not inserted:
                                data['Contact'] = user_id
                                data['Contact_Company_Role'] = [contact_dict[contact]]
                                data['Vendor'] = record_response[0]['details']['id']
                                request.append(data)
                if is_update:
                    contact_response = update_records('Vendors_X_Contacts', request)
                    if r.get('status_code') == 202:
                        contact_response = create_records('Vendors_X_Contacts', request)
                else:
                    contact_response = create_records('Vendors_X_Contacts', request)
        except Exception as exc:
            print(exc)
            exc_info = sys.exc_info()
            e = ''.join(traceback.format_exception(*exc_info))
            final_dict['exception'] = e
        final_list[license_db_id] = final_dict
    return final_list
            
@app.task(queue="general")
def insert_vendors(id=None, is_update=False, is_single_user=False):
    """
    Insert Vendors into Zoho CRM.
    """
    brand_id = None
    if is_single_user:
        return insert_record(id=id, is_update=is_update, is_single_user=is_single_user)
    else:
        final_list = dict()
        if id:
            records = License.objects.filter(id=id).select_related()
        else:
            records = License.objects.filter(is_updated_in_crm=False).select_related()
        for record in records:
            final_dict = dict()
            if is_update:
                result = search_query('Orgs', record.organization.name, 'Name')
                if result.get('status_code') == 200:
                    organization_id = result.get('response')[0].get('id')
                    result = update_records('Orgs', record.organization.__dict__, True)
                else:
                    result = create_records('Orgs', record.organization.__dict__, True)
                if result.get('status_code') in [200, 201]:
                    try:
                        organization_id = result['response'][0]['id']
                    except KeyError:
                        organization_id = result['response']['response']['data'][0]['details']['id']
            else:
                result = search_query('Orgs', record.organization.name, 'Name')
                if result.get('status_code') == 200:
                    organization_id = result['response'][0]['id']
                else:
                    result = create_records('Orgs', record.organization.__dict__, True)
                    if result.get('status_code') == 201:
                        organization_id = result['response']['response']['data'][0]['details']['id']
            try:
                if is_update:
                    result = search_query('Brands', record.brand.brand_name, 'Name')
                    if result.get('status_code') == 200:
                        result = update_records('Brands', record.__dict__, True)
                    else:
                        result = create_records('Brands', record.__dict__, True)
                    if result.get('status_code') in [200, 201]:
                        try:
                            brand_id = result['response'][0]['id']
                        except KeyError:
                            brand_id = result['response']['response']['data'][0]['details']['id']
                else:
                    result = search_query('Brands', record.brand.brand_name, 'Name')
                    if result.get('status_code') == 200:
                        brand_id = result['response'][0]['id']
                    else:
                        result = create_records('Brands', record.brand.__dict__, True)
                        if result.get('status_code') == 201:
                            brand_id = result['response']['response']['data'][0]['details']['id']
            except Exception as exc:
                print(exc)
                brand_id = None
                pass
            final_dict['org'] = organization_id
            final_dict['brand'] = brand_id
            if brand_id:
                try:
                    record_obj = Brand.objects.get(id=record.brand_id)
                    record_obj.zoho_crm_id = brand_id
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)
                    pass
            if organization_id:
                try:
                    record_obj = Organization.objects.get(id=record.organization_id)
                    record_obj.zoho_crm_id = organization_id
                    record_obj.is_updated_in_crm = True
                    record_obj.save()
                except KeyError as exc:
                    print(exc)
                    pass
            record_response = insert_record(record=record, is_update=is_update, is_single_user=is_single_user)
            final_dict.update(record_response)
            for k,response in record_response.items():
                if (brand_id or \
                    response['license']['status_code'] == 200 and \
                    response['vendor']['status_code'] in [200, 201] and \
                    organization_id):
                    data = dict()
                    resp_brand = brand_id
                    try:
                        resp_vendor = response['vendor']['response']['response']['data']
                        data['Vendor'] = resp_vendor[0]['details']['id']
                    except TypeError:
                        resp_vendor = response['vendor']['response'][0]
                        data['Vendor'] = resp_vendor['id']
                    data['Org'] = organization_id
                    data['Brand'] = brand_id
                    if is_update:
                        r = update_records('Orgs_X_Vendors', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Orgs_X_Vendors', [data])
                        final_dict['org_vendor'] = r

                        r = update_records('Orgs_X_Brands', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Orgs_X_Brands', [data])
                        final_dict['org_brand'] = r

                        r = update_records('Brands_X_Vendors', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Brands_X_Vendors', [data])
                        final_dict['brand_vendor'] = r
                    else:
                        r = create_records('Orgs_X_Vendors', [data])
                        final_dict['org_vendor'] = r
                        r = create_records('Orgs_X_Brands', [data])
                        final_dict['org_brand'] = r
                        r = create_records('Brands_X_Vendors', [data])
                        final_dict['brand_vendor'] = r
            final_list[record.id] = final_dict
            record.crm_output = {'output': final_dict}
            record.save()
        return final_list

def upload_file_s3_to_box(aws_bucket, aws_key):
    """
    Upload file from s3 to box.
    """
    aws_client = get_boto_client('s3')
    file_obj = aws_client.get_object(Bucket=aws_bucket, Key=aws_key)
    md5sum = aws_client.head_object(Bucket=aws_bucket,Key=aws_key)['ETag'][1:-1]
    if file_obj.get('Body'):
       data = file_obj['Body'].read()
       aws_md5 = hashlib.md5(data).hexdigest()
       aws_sha1 = hashlib.sha1(data).hexdigest()
       data = BytesIO(data)
       box_file_obj = upload_file_stream(TEMP_LICENSE_FOLDER, data, aws_key.split('/')[-1])
       if isinstance(box_file_obj, str):
           return box_file_obj
       if (md5sum == aws_md5) and (box_file_obj.sha1 == aws_sha1):
           aws_client.delete_object(Bucket=aws_bucket, Key=aws_key)
       else:
           print('Checksum didnot match.', aws_bucket, aws_key)
       return box_file_obj
    return None

def update_license(dba, license=None, license_id=None):
    """
    Update license with shareable link.
    """
    response = None
    data = list()
    if not license and license_id:
        try:
            license = License.objects.get(id=license_id)
        except License.DoesNotExist:
            return {'error': f'License {license_id} not in database'}
        license = license.__dict__
        license['license_db_id'] = license['id']
        license['id'] = license['zoho_crm_id']
    license_number = license['license_number']
    dir_name = f'{dba}_{license_number}'
    new_folder = create_folder(LICENSE_PARENT_FOLDER_ID, dir_name)
    license_folder = create_folder(new_folder, 'Licenses')
    if not license.get('uploaded_license_to') or license_id:
        try:
            license_to = Documents.objects.filter(object_id=license['license_db_id'], doc_type='license').first()
            license_to_path = license_to.path
            aws_bucket = AWS_BUCKET
            box_file = upload_file_s3_to_box(aws_bucket, license_to_path)
            if isinstance(box_file, str):
                file_id = box_file
            else:
                file_id = box_file.id
            moved_file = move_file(file_id, license_folder)
            license_url = get_shared_link(file_id)
            if license_url:
                license['uploaded_license_to'] = license_url + "?id=" + moved_file.id
                license_to.box_url = license_url
                license_to.box_id = moved_file.id
                license_to.save()
        except Exception as exc:
            print('Error in update license', exc)
            pass
    # documents = create_folder(new_folder, 'documents')
    if not license.get('uploaded_sellers_permit_to') or license_id:
        try:
            seller_to = Documents.objects.filter(object_id=license['license_db_id'], doc_type='seller_permit').first()
            seller_to_path = seller_to.path
            aws_bucket = AWS_BUCKET
            box_file = upload_file_s3_to_box(aws_bucket, seller_to_path)
            if isinstance(box_file, str):
                file_id = box_file
            else:
                file_id = box_file.id
            moved_file = move_file(file_id, license_folder)
            seller_permit_url = get_shared_link(file_id)
            if seller_permit_url:
                license['uploaded_sellers_permit_to'] = seller_permit_url + "?id=" + moved_file.id
                license_to.box_url = seller_permit_url
                license_to.box_id = moved_file.id
                license_to.save()
        except Exception as exc:
            print('Error in update license', exc)
            pass
    license_obj = License.objects.filter(pk=license['license_db_id']).update(
        uploaded_license_to=license.get('uploaded_license_to'),
        uploaded_sellers_permit_to=license.get('uploaded_sellers_permit_to')
    )
    data.append(license)
    response = update_records('Licenses', data)
    return response

def get_vendors_from_licenses(field, licenses):
    """
    Get vendor id from licenses.
    """
    vendor_lookup = licenses.get(field)
    if vendor_lookup:
        return vendor_lookup.get('id')

@app.task(queue="general")
def get_records_from_crm(license_number):
    """
    Get records from Zoho CRM using license number.
    """
    final_response = dict()
    licenses = search_query('Licenses', license_number, 'Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        for license_dict in licenses.get('response'):
            license_number = license_dict['Name']
            vendor_id = None
            account_id = None
            if license_dict.get('License_Type') in VENDOR_LICENSE_TYPES:
                vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
                if vendor['status_code'] != 200:
                    vendor_id = get_vendors_from_licenses('Vendor_Name_Lookup', license_dict)
                else:
                    vendor = vendor['response'][0]['Licenses_Module']
                    vendor_id = vendor['id']
                if not vendor_id:
                    account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
                    if account['status_code'] != 200:
                        account_id = get_vendors_from_licenses('Account_Name_Lookup', license_dict)
                    else:
                        account = account['response'][0]['Licenses_Module']
                        account_id = account['id']
                    if not account_id:
                        final_response[license_number] = {'error': 'No association found for legal business name'}
                        continue

            else:
                account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
                if account['status_code'] != 200:
                    account_id = get_vendors_from_licenses('Account_Name_Lookup', license_dict)
                else:
                    account = account['response'][0]['Licenses_Module']
                    account_id = account['id']
                if not account_id:
                    vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
                    if vendor['status_code'] != 200:
                        vendor_id = get_vendors_from_licenses('Vendor_Name_Lookup', license_dict)
                    else:
                        vendor = vendor['response'][0]['Licenses_Module']
                        vendor_id = vendor['id']
                    if not vendor_id:
                        final_response[license_number] = {'error': 'No association found for legal business name'}
                        continue
            if vendor_id:
                org = search_query('Orgs_X_Vendors', vendor_id, 'Vendor')
            elif account_id:
                org = search_query('Orgs_X_Accounts', account_id, 'Account')
            else:
                org = dict()
            if org.get('status_code') == 200:
                org_list = list()
                for o in org.get('response'):
                    r = dict()
                    if o.get('Org'):
                        r['name'] = o['Org']['name']
                        r['id'] = o['Org']['id']
                        org_list.append(r)
                final_response['organization'] = org_list
            else:
                final_response['organization'] = org
            if vendor_id:
                brand = search_query('Brands_X_Vendors', vendor_id, 'Vendor')
            elif account_id:
                brand = search_query('Brands_X_Accounts', account_id, 'Account')
            else:
                brand = dict()
            if brand.get('status_code') == 200:
                try:
                    brand_list = list()
                    for b in brand.get('response'):
                        r = dict()
                        r['name'] = b['Brand']['name']
                        r['id'] = b['Brand']['id']
                        brand_list.append(r)
                    final_response['Brand'] = brand_list
                except TypeError:
                    pass
            else:
                final_response['Brand'] = brand
            crm_obj = get_crm_obj()
            if vendor_id:
                record = crm_obj.get_record('Vendors', vendor_id)
            elif account_id:
                record = crm_obj.get_record('Accounts', account_id)
            if record['status_code'] == 200:
                if vendor_id:
                    vendor = record['response'][vendor_id]
                elif account_id:
                    vendor = record['response'][account_id]
                # licenses = [licenses['response'][0]]
                licenses = license_dict
                if vendor.get('Licenses'):
                    license_list = vendor.get('Licenses').split(',')
                    license_list.remove(license_number)
                    for l in license_list:
                        license = search_query('Licenses', l.strip(), 'Name')
                        if license['status_code'] == 200:
                            license_dict.append(license['response'][0])
                        else:
                            license_dict.append(license)
                crm_dict = get_format_dict('Licenses_To_DB')
                r = dict()
                for k, v in crm_dict.items():
                    r[k] = licenses.get(v)
                response = dict()
                if vendor_id:
                    crm_dict = get_format_dict('Vendors_To_DB')
                    response['vendor_type'] = get_vendor_types(vendor['Vendor_Type'], True)
                elif account_id:
                    crm_dict = get_format_dict('Accounts_To_DB')
                    response['vendor_type'] = get_vendor_types(vendor['Company_Type'], True)
                response['license'] = r
                record_dict = dict()
                for k,v in crm_dict.items():
                    if v.endswith('_parse'):
                        value = v.split('_parse')[0]
                        if vendor_id:
                            value = parse_fields('Vendors', k, value, vendor, crm_obj, vendor_id=vendor_id)
                        elif account_id:
                            value = parse_fields('Accounts', k, value, vendor, crm_obj, account_id=account_id)
                        record_dict[k] = value
                    else:
                        record_dict[k] = vendor.get(v)
                if vendor_id:
                    record_dict['profile_id'] = vendor_id
                    response['is_seller'] = True
                    response['is_buyer'] = False
                elif account_id:
                    record_dict['profile_id'] = account_id
                    response['is_seller'] = False
                    response['is_buyer'] = True
                response['license_profile'] = record_dict
                final_response[license_number] = response
        return final_response
    return licenses

def get_vendor_from_contact(contact_email):
    """
    Return vendor information using contact email.
    """
    response = dict()
    contact_details = search_query('Contacts', contact_email, 'Email')
    if contact_details['status_code'] == 200:
        response['contact_company_role'] = contact_details['response'][0]['Contact_Company_Role']
        vendor_details = search_query(
            'Vendors_X_Contacts',
            contact_details['response'][0]['id'],
            'Contact')
        if vendor_details['status_code'] == 200:
            vendor_id = vendor_details['response'][0]['Vendor']['id']
            response['vendor'] = get_record('Vendors', vendor_id)['response']
            response['code'] = 0
            return response
    return {'code': 1, 'error': 'No data found'}

def list_crm_contacts(contact_id=None):
    """
    Return contacts from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    if contact_id:
        return crm_obj.get_record('Contacts', contact_id)
    return crm_obj.get_records('Contacts')

def insert_account_record(record=None, is_update=False, id=None, is_single_user=False):
    """
    Insert account to Zoho CRM.
    """
    if id and is_single_user:
        licenses = [License.objects.select_related().get(id=id).__dict__]
    else:
        licenses = [record.__dict__]
    final_list = dict()
    for i in licenses:
        final_dict = dict()
        l = list()
        d = dict()
        d.update(i)
        license_db_id= i['id']
        d.update({'license_db_id': license_db_id})
        license_db = License.objects.select_related().get(id=license_db_id)
        licenses = get_licenses(i['legal_business_name'])
        d.update(license_db.license_profile.__dict__)
        try:
            d.update(license_db.profile_contact.profile_contact_details)
        except Exception:
                pass
        vendor_id = license_db.license_profile.__dict__['id']
        try:
            for k, v in license_db.cultivation_overview.__dict__.items():
                d.update({'co.' + k:v})
        except Exception:
            pass
        try:
            for k, v in license_db.financial_overview.__dict__.items():
                d.update({'fo.' + k:v})
        except Exception:
            pass
        try:
            for k, v in license_db.crop_overview.__dict__.items():
                d.update({'cr.' + k:v})
        except Exception:
            pass
        d.update({'id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
        l.append(d['id'])
        d.update({'licenses': l})    
        if id and is_single_user and is_update:
            d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
        # farm_name = license_db.license_profile.__dict__['name']
        farm_name = i['legal_business_name']
        if d['is_seller'] == True:
                continue
        response = update_license(dba=farm_name, license=d)
        final_dict['license'] = response
        if response['status_code'] == 200:
            record_response = response['response']['data']
            try:
                record_obj = License.objects.get(id=license_db_id)
                record_obj.zoho_crm_id = record_response[0]['details']['id']
                record_obj.is_updated_in_crm = True
                record_obj.save()
            except KeyError as exc:
                print(exc)
                pass
        if is_update:
                d['id'] = license_db.license_profile.__dict__['zoho_crm_id']
                if d['id']:
                    r = search_query('Accounts', d['name'], 'Account_Name')
                    if r.get('status_code') == 200:
                        d['id'] = r.get('response')[0]['id']
                if d['id']:
                    result = update_records('Accounts', d, is_return_orginal_data=True)
                else:
                    result = create_records('Accounts', d, True)
        else:
            result = search_query('Accounts', d['name'], 'Account_Name')
            if result.get('status_code') != 200:
                result = create_records('Accounts', d, is_return_orginal_data=True)
            else:
                d['id'] = result.get('response')[0]['id']
                result = update_records('Accounts', d, True)
        final_dict['account'] = result
        if response['status_code'] == 200 and result['status_code'] in [200, 201]:
            record_response = result['response']['response']['data']
            try:
                record_obj = LicenseProfile.objects.get(id=vendor_id)
                record_obj.zoho_crm_id = record_response[0]['details']['id']
                record_obj.is_updated_in_crm = True
                record_obj.save()
            except KeyError as exc:
                print(exc)
                pass
            if (result['response']['orignal_data'][0].get('Licenses_List')):
                data = dict()
                data['Licenses_Module'] = record_response[0]['details']['id']
                for license in result['response']['orignal_data'][0]['Licenses_List']:
                    data['Licenses'] = license
                    if is_update:
                        r = update_records('Accounts_X_Licenses', [data])
                        if r.get('status_code') == 202:
                            r = create_records('Accounts_X_Licenses', [data])
                    else:
                        r = create_records('Accounts_X_Licenses', [data])
                request = list()
                contact_dict = {
                    'Owner1': 'Owner',
                    'Contact_1': 'Cultivation Manager',
                    'Contact_2': 'Logistics Manager',
                    'Contact_3': 'Sales Manager'}
                for contact in ['Owner1', 'Contact_1', 'Contact_2', 'Contact_3']:
                    data = dict()
                    user_id = result['response']['orignal_data'][0].get(contact)
                    if user_id:
                        if len(request) == 0:
                            data['Contacts'] = user_id
                            data['Contact_Company_Role'] = [contact_dict[contact]]
                            data['Accounts'] = record_response[0]['details']['id']
                            request.append(data)
                        else:
                            inserted = False
                            for j in request:
                                if j.get('Contacts') == user_id:
                                    j['Contact_Company_Role'].append(contact_dict[contact])
                                    inserted = True
                            if not inserted:
                                data['Contacts'] = user_id
                                data['Contact_Company_Role'] = [contact_dict[contact]]
                                data['Accounts'] = record_response[0]['details']['id']
                                request.append(data)
                if is_update:
                    contact_response = update_records('Accounts_X_Contacts', request)
                    if r.get('status_code') == 202:
                        contact_response = create_records('Accounts_X_Contacts', request)
                else:
                    contact_response = create_records('Accounts_X_Contacts', request)
        final_list[license_db_id] = final_dict
    return final_list

@app.task(queue="general")
def insert_accounts(id=None, is_update=False, is_single_user=False):
    """
    Insert new accounts in Zoho CRM.
    """
    brand_id = None
    if is_single_user:
        return insert_account_record(id=id, is_single_user=is_single_user)
    else:
        final_list = dict()
        if id:
            records = License.objects.filter(id=id).select_related()
        else:
            records = License.objects.filter(is_updated_in_crm=False).select_related()
        for record in records:
            final_dict = dict()
            try:
                if is_update:
                    result = search_query('Orgs', record.organization.name, 'Name')
                    if result.get('status_code') == 200:
                        organization_id = result.get('response')[0].get('id')
                        result = update_records('Orgs', record.organization.__dict__, True)
                    else:
                        result = create_records('Orgs', record.organization.__dict__, True)
                    if result.get('status_code') in [200, 201]:
                        try:
                            organization_id = result['response'][0]['id']
                        except KeyError:
                            organization_id = result['response']['response']['data'][0]['details']['id']
                else:
                    result = search_query('Orgs', record.organization.name, 'Name')
                    if result.get('status_code') == 200:
                        organization_id = result['response'][0]['id']
                    else:
                        result = create_records('Orgs', record.organization.__dict__, True)
                        if result.get('status_code') == 201:
                            organization_id = result['response']['response']['data'][0]['details']['id']
                try:
                    if is_update:
                        result = search_query('Brands', record.brand.brand_name, 'Name')
                        if result.get('status_code') == 200:
                            result = update_records('Brands', record.brand.__dict__, True)
                        else:
                            result = create_records('Brands', record.brand.__dict__, True)
                        if result.get('status_code') in [200, 201]:
                            try:
                                brand_id = result['response'][0]['id']
                            except KeyError:
                                brand_id = result['response']['response']['data'][0]['details']['id']
                    else:
                        result = search_query('Brands', record.brand.brand_name, 'Name')
                        if result.get('status_code') == 200:
                            brand_id = result['response'][0]['id']
                        else:
                            result = create_records('Brands', record.brand.__dict__, True)
                            if result.get('status_code') == 201:
                                brand_id = result['response']['response']['data'][0]['details']['id']
                except Exception as exc:
                    print(exc)
                    brand_id = None
                    pass
                final_dict['org'] = organization_id
                final_dict['brand'] = brand_id
                if brand_id:
                    try:
                        record_obj = Brand.objects.get(id=record.brand_id)
                        record_obj.zoho_crm_id = brand_id
                        record_obj.is_updated_in_crm = True
                        record_obj.save()
                    except KeyError as exc:
                        print(exc)
                        pass
                if organization_id:
                    try:
                        record_obj = Organization.objects.get(id=record.organization_id)
                        record_obj.zoho_crm_id = organization_id
                        record_obj.is_updated_in_crm = True
                        record_obj.save()
                    except KeyError as exc:
                        print(exc)
                        pass
                record_response = insert_account_record(record=record, is_update=is_update, is_single_user=is_single_user)
                final_dict.update(record_response)
                for k, response in record_response.items():
                    if (brand_id or \
                        response['license']['status_code'] == 200 and \
                        response['account']['status_code'] in [200, 201] and organization_id):
                        data = dict()
                        resp_brand = brand_id
                        try:
                            resp_account = response['account']['response']['response']['data']
                            data['Account'] = resp_account[0]['details']['id']
                        except TypeError:
                            resp_account = response['account']['response'][0]
                            data['Account'] = resp_account['id']
                        data['Org'] = organization_id
                        data['Brand'] = brand_id
                        if is_update:
                            r = update_records('Orgs_X_Accounts', [data])
                            if r.get('status_code') == 202:
                                r = create_records('Orgs_X_Accounts', [data])
                            final_dict['org_account'] = r

                            r = update_records('Orgs_X_Brands', [data])
                            if r.get('status_code') == 202:
                                r = create_records('Orgs_X_Brands', [data])
                            final_dict['org_brand'] = r

                            r = update_records('Brands_X_Accounts', [data])
                            if r.get('status_code') == 202:
                                r = create_records('Brands_X_Accounts', [data])
                            final_dict['brand_account'] = r
                        else:
                            r = create_records('Orgs_X_Accounts', [data])
                            final_dict['org_account'] = r
                            r = create_records('Orgs_X_Brands', [data])
                            final_dict['org_brand'] = r
                            r = create_records('Brands_X_Accounts', [data])
                            final_dict['brand_account'] = r
            except Exception as exc:
                print(exc)
                exc_info = sys.exc_info()
                e = ''.join(traceback.format_exception(*exc_info))
                final_dict['exception'] = e
            final_list[record.id] = final_dict
            record.crm_output = {'output': final_dict}
            record.save()
        return final_list

@app.task(queue="general")
def get_accounts_from_crm(legal_business_name):
    """
    Fetch existing accounts from Zoho CRM.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        license_number = licenses['response'][0]['Name']
        account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
        if account['status_code'] != 200:
            account_id = get_vendors_from_licenses('Account_Name_Lookup', licenses)
        else:
            account = account['response'][0]['Licenses_Module']
            account_id = account['id']
        if not account_id:
            return {'error': 'No association found for legal business name'}
        crm_obj = get_crm_obj()
        account_record = crm_obj.get_record('Accounts', account_id)
        if account_record['status_code'] == 200:
            account = account_record['response'][account_id]
            licenses = [licenses['response'][0]]
            if account.get('Licenses'):
                license_list = account.get('Licenses').split(',')
                license_list.remove(license_number)
                for l in license_list:
                    license = search_query('Licenses', l.strip(), 'Name')
                    if license['status_code'] == 200:
                        licenses.append(license['response'][0])
            crm_dict = get_format_dict('Licenses_To_DB')
            li = list()
            for license in licenses:
                r = dict()
                for k, v in crm_dict.items():
                    r[k] = license.get(v)
                li.append(r)
            crm_dict = get_format_dict('Accounts_To_DB')
            response = dict()
            response['licenses'] = li
            for k,v in crm_dict.items():
                if v.endswith('_parse'):
                    value = v.split('_parse')[0]
                    value = parse_fields('Accounts', k, value, account, crm_obj, account_id=account_id)
                    response[k] = value
                else:
                    response[k] = account.get(v)
            return response
    return {}


def get_vendors_from_crm(legal_business_name):
    """
    Fetch existing vendors from Zoho CRM.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        license_number = licenses['response'][0]['Name']
        vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
        if vendor['status_code'] != 200:
            vendor_id = get_vendors_from_licenses('Vendor_Name_Lookup', licenses)
        else:
            vendor = vendor['response'][0]['Licenses_Module']
            vendor_id = vendor['id']
        if not vendor_id:
            return {'error': 'No association found for legal business name'}
        crm_obj = get_crm_obj()
        vendor_record = crm_obj.get_record('Vendors', vendor_id)
        if vendor_record['status_code'] == 200:
            vendor = vendor_record['response'][vendor_id]
            licenses = [licenses['response'][0]]
            if vendor.get('Licenses'):
                license_list = vendor.get('Licenses').split(',')
                license_list.remove(license_number)
                for l in license_list:
                    license = search_query('Licenses', l.strip(), 'Name')
                    if license['status_code'] == 200:
                        licenses.append(license['response'][0])
            crm_dict = get_format_dict('Licenses_To_DB')
            li = list()
            for license in licenses:
                r = dict()
                for k, v in crm_dict.items():
                    r[k] = license.get(v)
                li.append(r)
            crm_dict = get_format_dict('Vendors_To_DB')
            response = dict()
            response['licenses'] = li
            for k,v in crm_dict.items():
                if v.endswith('_parse'):
                    value = v.split('_parse')[0]
                    value = parse_fields('Vendors', k, value, vendor, crm_obj, vendor_id=vendor_id)
                    response[k] = value
                else:
                    response[k] = vendor.get(v)
            return response
    return {}

def post_leads_to_slack_and_email(record,response):
    """
    Post New leads on slack.
    """
    try:
        lead_crm_link = settings.ZOHO_CRM_URL+"/crm/org"+settings.CRM_ORGANIZATION_ID+"/tab/Leads/"+response.get('response')['data'][0]['details']['id']+"/"
        msg = """New lead is added via connect page with the details as:\n- First Name:%s\n- Last Name:%s\n- Company Name:%s\n -Title:%s\n- Vendor Category:%s\n- Heard From:%s\n- Phone:%s\n- Message:%s\n- Email:%s\n- Lead Origin:%s\n- Lead CRM Link:<%s> """ %(record.get("first_name"),record.get("last_name"),record.get("company_name"),record.get("title"),','.join(record.get("vendor_category")),record.get("heard_from"),record.get("phone"),record.get("message"),record.get("email"),record.get("Lead_Origin"),lead_crm_link)
        slack.chat.post_message(settings.SLACK_SALES_CHANNEL,msg, as_user=False, username=settings.BOT_NAME, icon_url=settings.BOT_ICON_URL)
        mail_send("connect.html",{'first_name': record.get("first_name"),'last_name':record.get("last_name"),'mail':record.get("email"),'company_name':record.get("company_name"),'title':record.get("title"),'vendor_category':','.join(record.get("vendor_category")),'heard_from':record.get("heard_from"),'phone':record.get("phone"),'message':record.get("message"),'lead_origin':record.get("Lead_Origin"),'lead_crm_link':lead_crm_link},"New lead via connect page.",'connect@thrive-society.com')
    except Exception as e:
        print("Exception while posting to slack & email on lead creation.")
    

@app.task(queue="general")
def create_lead(record):
    """
    Create lead in Zoho CRM.
    """
    record.update({"Lead_Origin":"Connect Form"})
    response = create_records('Leads', record)
    post_leads_to_slack_and_email(record,response)
    return response

def get_field(record, key, field):
    """
    Parse crm fields.
    """
    date_fields = [
        # 'Date_Harvested',
        'Date_Received',
        'Date_Reported',
        'Date_Tested',
        # 'Created_Time',
        'Last_Activity_Time',
        # 'Modified_Time',
    ]
    labtest_float_values = ['THC', 'CBD', 'THCA',
                            'THCVA', 'THCV', 'CBDA',
                            'CBGA', 'CBG', 'CBN',
                            'CBL', 'CBCA', 'CBC', 'CBDV',
                            'Cannabinoids', 'Total_CBD', 'CBDVA',
                            'Total_Cannabinoids', 'Total_THC',
                            'd_8_THC', 'Total_CBD']
    if field in labtest_float_values:
        v = record.get(field)
        if '%' in v:
            v = v.strip('%')
        if v == 'NA':
            v = "-1"
        elif v == 'ND':
            v = "-2"
        elif v == 'NT':
            v = "-3"
        return float(v)
    if field in ('Created_By', 'Modified_By'):
        return record.get(key)
    if field in ('parent_1', 'parent_2'):
        return [record.get(key).get('name')]
    if field in ('Created_Time', 'Date_Harvested', 'Modified_Time'):
        return datetime.strptime(record.get(key), '%Y-%m-%dT%H:%M:%S%z').date()
    if field in date_fields:
        return datetime.strptime(record.get(key), '%Y-%m-%d')

def parse_crm_record(module, records):
    """
    Parse crm record.
    """
    record_list = list()
    crm_obj = get_crm_obj()
    crm_dict = get_format_dict(module)
    for record in records:
        record_dict = dict()
        for k,v in crm_dict.items():
            try:
                if v.endswith('_parse'):
                    key = v.split('_parse')
                    value = get_field(record, k, key[0])
                    record_dict[key[0]] = value
                else:
                    record_dict[v] = record.get(k)
            except Exception as exc:
                continue
        record_list.append(record_dict)
    return record_list

def sync_cultivars(record):
    """
    Webhook for Zoho CRM to sync cultivars real time.
    """
    crm_obj = get_crm_obj()
    record = json.loads(record.dict()['response'])
    record = parse_crm_record('Cultivars', [record])[0]
    record['status'] = 'approved'
    try:
        obj, created = Cultivar.objects.update_or_create(
            cultivar_crm_id=record['cultivar_crm_id'],
            cultivar_name=record['cultivar_name'],
            defaults=record)
        return created
    except Exception as exc:
        print(exc)
        return {}

def fetch_cultivars(days=1):
    """
    Fetch cultivars from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S%z')
    request_headers = dict()
    request_headers['If-Modified-Since'] = date
    has_more = True
    page = 0
    while has_more != False:
        records = crm_obj.get_records(module='Cultivars', page=page, extra_headers=request_headers)['response']
        has_more = records['info']['more_records']
        page = records['info']['page'] + 1
        records = parse_crm_record('Cultivars', records['data'])
        for record in records:
            try:
                obj, created = Cultivar.objects.update_or_create(
                    cultivar_crm_id=record['cultivar_crm_id'], cultivar_name=record['cultivar_name'], defaults=record)
            except Exception as exc:
                print(exc)
                continue
    return

def get_labtest(id=None, sku=None):
    """
    Fetch labtest from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    if id:
        response = crm_obj.get_full_record('Testing', id)
    else:
        response = search_query('Testing', sku, 'Inventory_SKU')
    if response['status_code'] != 200:
        return response
    if id:
        response = parse_crm_record('Testing', [response['response']])
    elif sku:
        response = parse_crm_record('Testing', [response['response'][id]])
    return {'status_code': 200,
            'response': response}
    
def fetch_labtests(days=1):
    """
    Fetch labtests from Zoho CRM.
    """
    crm_obj = get_crm_obj()
    yesterday = datetime.now() - timedelta(days=days)
    date = datetime.strftime(yesterday, '%Y-%m-%dT%H:%M:%S%z')
    request_headers = dict()
    request_headers['If-Modified-Since'] = date
    has_more = True
    page = 0
    while has_more != False:
        records = crm_obj.get_records(module='Testing', page=page, extra_headers=request_headers)
        if records.get('response'):
            records = records['response']
            has_more = records['info']['more_records']
            page = records['info']['page'] + 1
            records = parse_crm_record('Testing', records['data'])
            for record in records:
                try:
                    obj, created = LabTest.objects.update_or_create(
                        labtest_crm_id=record['labtest_crm_id'], Inventory_SKU=record['Inventory_SKU'], defaults=record)
                except Exception as exc:
                    print(exc)
                    continue
    return

def sync_labtest(record):
    """
    Webhook for Zoho CRM to sync labtest real time.
    """
    crm_obj = get_crm_obj()
    record = json.loads(record.dict()['response'])
    record = parse_crm_record('Testing', [record])[0]
    try:
        obj, created = LabTest.objects.update_or_create(
            labtest_crm_id=record['labtest_crm_id'],
            Name=record['Name'],
            defaults=record)
        return created
    except Exception as exc:
        print(exc)
        return {}

def fetch_licenses():
    """
    Fetch licenses and update in database.
    """
    success_count = 0
    error_count = 0
    error_licenses = list()
    success_licenses = list()
    licenses = License.objects.all()
    for license in licenses:
        crm_license = search_query('Licenses', license.license_number, 'Name')
        crm_license = crm_license.get('response')
        if crm_license and len(crm_license) > 0:
            for l in crm_license:
                try:
                    if l['Name'] == license.license_number and l['id'] == license.zoho_crm_id:
                        if license.expiration_date != l['Expiration_Date'] and \
                            license.issue_date != l['Issue_Date']:
                            license.expiration_date = l['Expiration_Date']
                            license.issue_date = l['Issue_Date']
                            license.is_updated_via_trigger = True
                            license.save()
                            success_count += 1
                            success_licenses.append(license.license_number)
                except Exception as exc:
                    print(exc)
                    continue
        else:
            print('license not found in database -', license.license_number)
            error_count += 1
            error_licenses.append(license.license_number)
    return {'success_count': success_count, 'error_count': error_count}

def update_program_selection(record_id, tier_selection):
    """
    Sync program selection from crm to webapp.
    """
    try:
        license_profile = LicenseProfile.objects.get(zoho_crm_id=record_id)
        try:
            license_profile.license.program_overview
        except License.program_overview.RelatedObjectDoesNotExist:
            ProgramOverview.objects.create(license=license_profile.license)
        license_profile.license.program_overview.program_details = {'program_name': tier_selection}
        license_profile.license.program_overview.save()
        return {'code': 0, 'message': 'Success'}
    except LicenseProfile.DoesNotExist:
        error = {'code': 1, 'error': f'Vendor {record_id} not in database.'}
        print(error)
        return error

def fetch_record_owners(license_number=None, update_all=False):
    """
    Fetch vendor/account owner for license_number or
    Fetch owner for all records which don't have owner in db.
    """
    vendor_id = None
    account_id = None
    final_response = dict()
    if license_number:
        records = License.objects.filter(license_number=license_number)
    elif update_all:
        records = License.objects.filter(license_profile__crm_owner_id__isnull=True)
    for record in records:
        full_record = dict()
        license_number = record.license_number
        licenses = search_query('Licenses', license_number, 'Name')
        if licenses['status_code'] == 200 and len(licenses['response']) > 0:
            for license_dict in licenses.get('response'):
                vendor = search_query('Vendors_X_Licenses', license_number, 'Licenses')
                if vendor['status_code'] != 200:
                    vendor_id = get_vendors_from_licenses('Vendor_Name_Lookup', license_dict)
                else:
                    vendor = vendor['response'][0]['Licenses_Module']
                    vendor_id = vendor['id']
                if not vendor_id:
                    account = search_query('Accounts_X_Licenses', license_number, 'Licenses')
                    if account['status_code'] != 200:
                        account_id = get_vendors_from_licenses('Account_Name_Lookup', license_dict)
                    else:
                        account = account['response'][0]['Licenses_Module']
                        account_id = account['id']
                    if not account_id:
                        final_response[license_number] = {'error': 'No association found for legal business name'}
                        continue
        crm_obj = get_crm_obj()
        if vendor_id:
            full_record = crm_obj.get_full_record('Vendors', vendor_id)
        elif account_id:
            full_record = crm_obj.get_full_record('Accounts', account_id)
        else:
            continue
        if full_record.get('status_code') == 200:
            owner = full_record.get('response').get('Owner')
            try:
                license_profile = LicenseProfile.objects.get(id=record.license_profile.id)
            except LicenseProfile.DoesNotExist:
                final_response[license_number] = {'error': 'License does not exist in database.'}
                continue
            license_profile.crm_owner_id = owner.get('id')
            license_profile.crm_owner_email = owner.get('email')
            license_profile.save()
            final_response[license_number] = license_profile
    return final_response


def get_vendor_associations(vendor_id, organizations=True, brands=True, licenses=True, contacts=True, cultivars=True):
    final_response = {}
    if organizations:
        final_response['Orgs'] = []
        org = search_query('Orgs_X_Vendors', vendor_id, 'Vendor')
        if org.get('status_code') == 200:
            for o in org.get('response'):
                r = dict()
                r['name'] = o['Org']['name']
                r['id'] = o['Org']['id']
                final_response['Orgs'].append(r)
    if brands:
        final_response['Brands'] = []
        brand = search_query('Brands_X_Vendors', vendor_id, 'Vendor')
        if brand.get('status_code') == 200:
            for b in brand.get('response'):
                r = dict()
                r['name'] = b['Brand']['name']
                r['id'] = b['Brand']['id']
                final_response['Brands'].append(r)
    if licenses:
        final_response['Licenses'] = []
        license = search_query('Vendors_X_Licenses', vendor_id, 'Licenses_Module')
        if license.get('status_code') == 200:
            for l in license.get('response'):
                r = dict()
                r['name'] = l['Licenses']['name']
                r['id'] = l['Licenses']['id']
                final_response['Licenses'].append(r)
    if contacts:
        final_response['Contacts'] = []
        contact = search_query('Vendors_X_Contacts', vendor_id, 'Vendor')
        if contact.get('status_code') == 200:
            for ct in contact.get('response'):
                r = dict()
                r['name'] = ct['Contact']['name']
                r['id'] = ct['Contact']['id']
                r['roles'] = ct['Contact_Company_Role']
                r['linking_module_id'] = ct['id']
                final_response['Contacts'].append(r)
    if cultivars:
        final_response['Cultivars'] = []
        cultivar = search_query('Vendors_X_Cultivars', vendor_id, 'Cultivar_Associations')
        final_response['cultivar'] = []
        if cultivar.get('status_code') == 200:
            for cl in cultivar.get('response'):
                r = dict()
                r['name'] = cl['Cultivars']['name']
                r['id'] = cl['Cultivars']['id']
                final_response['Cultivars'].append(r)
    return final_response



def get_account_associations(account_id, organizations=True, brands=True, licenses=True, contacts=True):
    final_response = {}
    if organizations:
        final_response['Orgs'] = []
        org = search_query('Orgs_X_Accounts', account_id, 'Account')
        if org.get('status_code') == 200:
            for o in org.get('response'):
                r = dict()
                r['name'] = o['Org']['name']
                r['id'] = o['Org']['id']
                final_response['Orgs'].append(r)
    if brands:
        final_response['Brands'] = []
        brand = search_query('Brands_X_Accounts', account_id, 'Account')
        if brand.get('status_code') == 200:
            for b in brand.get('response'):
                r = dict()
                r['name'] = b['Brand']['name']
                r['id'] = b['Brand']['id']
                final_response['Brands'].append(r)
    if licenses:
        final_response['Licenses'] = []
        license = search_query('Accounts_X_Licenses', account_id, 'Licenses_Module')
        if license.get('status_code') == 200:
            for l in license.get('response'):
                r = dict()
                r['name'] = l['Licenses']['name']
                r['id'] = l['Licenses']['id']
                final_response['Licenses'].append(r)
    if contacts:
        final_response['Contacts'] = []
        contact = search_query('Accounts_X_Contacts', account_id, 'Accounts')
        if contact.get('status_code') == 200:
            for ct in contact.get('response'):
                r = dict()
                r['name'] = ct['Contacts']['name']
                r['id'] = ct['Contacts']['id']
                r['roles'] = ct['Contact_Company_Role']
                r['linking_module_id'] = ct['id']
                final_response['Contacts'].append(r)
    return final_response

def create_or_update_org_in_crm(org_obj):
    result = search_query('Orgs', org_obj.__dict__['name'], 'Name')
    if result.get('status_code') == 200:
        organization_id = result.get('response')[0].get('id')
        result = update_records('Orgs', org_obj.__dict__, True)
        if organization_id and org_obj.zoho_crm_id != organization_id:
            org_obj.zoho_crm_id = organization_id
            org_obj.save()
    else:
        try:
            result = create_records('Orgs', org_obj.__dict__)
        except Exception as exc:
                print('Error while creating Organization in Zoho CRM')
                print(exc)
        if result.get('status_code') in [200, 201]:
            try:
                organization_id = result['response'][0]['id']
            except KeyError:
                try:
                    organization_id = result['response']['data'][0]['details']['id']
                except KeyError:
                    organization_id = None
            if organization_id:
                org_obj.zoho_crm_id = organization_id
                org_obj.save()
            else:
                print('Error while Extrating zoho_crm_id for created Organization in Zoho CRM')
                print(result)
        else:
            print('Error while creating Organization in Zoho CRM')
            print(result)
