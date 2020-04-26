import ast
from pyzoho import CRM
from core.settings import (PYZOHO_CONFIG,
    PYZOHO_REFRESH_TOKEN,
    PYZOHO_USER_IDENTIFIER)
from user.models import (User, )
from vendor.models import (VendorProfile, )
from .crm_format import (CRM_FORMAT, )
from .box import (get_shared_link, )

def get_crm_obj():
    """
    Return ZCRM object.
    """
    return CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)

def get_picklist(module, field_name):
    """
    Return picklist for field.
    """
    crm_obj = get_crm_obj()
    module = crm_obj.get_module(module)['response']
    fields = module.get_all_fields().response_json['fields']
    for field in fields:
        if field['field_label'] == field_name and field['data_type'] in ('picklist', 'multiselectpicklist'):
            return field['pick_list_values']
    return list()
            
 
def get_format_dict(module):
    """
    Return Contact-CRM fields dictionary.
    """
    return CRM_FORMAT[module]

def parse_fields(key, value, obj, crm_obj):
    """
    Parse fields
    """
    def get_dict(cd, i):
        user = dict()
        for k,v in cd.items():
            user[k] = i.get(v)
        user = create_records('Contacts', [user])
        if user['status_code'] in (201, 202):
            return user['response']['data'][0]['details']['id']
        
    if value in ('ethics_and_certifications'):
        return ast.literal_eval(obj.get(value))
    if value.startswith('cultivars_'):
        try:
            c = value.split('_')
            d = obj.get(c[0])
            if d:
                return d[int(c[1])-1]['harvest_date']
        except Exception:
            return []
    if value.startswith('employees'):
        user = None
        d = obj.get(value)
        cd = {
            'last_name': 'employee_name',
            'email': 'employee_email',
            'phone': 'phone',
        }
        try:
            for i in d:
                if 'Cultivation Manager' in i['roles'] and key == 'Contact_1':
                    user = get_dict(cd, i)
                elif 'Logistics Manager' in i['roles'] and key == 'Contact_2':
                    user = get_dict(cd, i)
                elif 'Q&A Manager' in i['roles'] and key == 'Contact_3':
                    user = get_dict(cd, i)
                elif 'Owner' in i['roles'] and key == 'Owner1':
                    user = get_dict(cd, i)
            return user
        except IndexError:
            return []
        
def create_records(module, records, is_return_orginal_data=False):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    if isinstance(records, dict):
        records = [records]
    for record in records:
        contact_dict = dict()
        contact_crm_dict = get_format_dict(module)
        for k,v in contact_crm_dict.items():
            if v.endswith('_parse'):
                v = v.split('_parse')[0]
                v = parse_fields(k, v, record, crm_obj)
                contact_dict[k] = v
            else:
                contact_dict[k] = record.get(v)
        request.append(contact_dict)
    response = crm_obj.insert_records(module, request, is_return_orginal_data)
    return response

def update_records(module, records, is_return_orginal_data=False):
    response = dict()
    crm_obj = get_crm_obj()
    request = list()
    for record in records:
        contact_dict = dict()
        contact_crm_dict = get_format_dict(module)
        for k,v in contact_crm_dict.items():
            if v.endswith('_parse'):
                v = v.split('_parse')[0]
                v = parse_fields(k, v, record, crm_obj)
                contact_dict[k] = v
            else:
                contact_dict[k] = record.get(v)
        request.append(contact_dict)
    response = crm_obj.update_records(module, request, is_return_orginal_data)
    return response


def search_query(module, query, criteria):
    crm_obj = CRM(PYZOHO_CONFIG,
        PYZOHO_REFRESH_TOKEN,
        PYZOHO_USER_IDENTIFIER)
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

def insert_vendors():
    """
    Insert Vendors into Zoho CRM.
    """
    data_list = list()
    records = VendorProfile.objects.filter(is_updated_in_crm=False).select_related()
    for record in records:
        r = dict()
        r['db_id'] = record.id
        if record.license_set.values():
            l = list()
            for i in record.license_set.values():
                d = dict()
                licenses = get_licenses(i['legal_business_name'])
                d.update({'license_id':licenses[0]['id'], 'Owner':licenses[0]['Owner']['id']})
                d.update(i)
                update_license(d)
                l.extend(licenses)
            r.update({'licenses': l})
            r.update({'uploaded_sellers_permit_to': i['uploaded_sellers_permit_to']})
        try:
            r.update(record.profile_contact.profile_contact_details)
            r.update(record.profile_overview.profile_overview)
            r.update(record.financial_overview.financial_details)
            r.update(record.processing_overview.processing_config)
            if r.get('uploaded_sellers_permit_to'):
                license_url = get_shared_link(r.get('uploaded_sellers_permit_to'))
                r['Sellers_Permit'] = license_url
            data_list.append(r)
        except Exception:
            continue
    if len(data_list) > 0:
        result = create_records('Vendors', data_list, True)
        if result['status_code'] == 201:
            record_response = result['response']['response']['data']
            for i, record in enumerate(records):
                try:
                    record.zoho_crm_id = record_response[i]['details']['id']
                    record.is_updated_in_crm = True
                    record.save()
                except KeyError:
                    continue
                if (result['response']['orignal_data'][i].get('Licenses_List')):
                    data = dict()
                    data['Licenses_Module'] = record_response[i]['details']['id']
                    for license in result['response']['orignal_data'][i]['Licenses_List']:
                        data['Licenses'] = license
                        r = create_records('Vendors_X_Licenses', [data])
                data = dict()
                data['Cultivar_Associations'] = record_response[i]['details']['id']
                data['Cultivars'] = result['response']['orignal_data'][i]['cultivars']
                r = create_records('Vendors_X_Cultivars', [data])
        return result
    return {}

def update_license(license):
    """
    Update license with shareable link.
    """
    data = list()
    license_url = get_shared_link(license['uploaded_license_to'])
    license['uploaded_license_to'] = license_url
    data.append(license)
    response = update_records('Licenses', data)
    return response

def get_records_from_crm(legal_business_name):
    """
    Get records from Zoho CRM using legal business name.
    """
    licenses = search_query('Licenses', legal_business_name, 'Legal_Business_Name')
    if licenses['status_code'] == 200 and len(licenses['response']) > 0:
        crm_obj = get_crm_obj()
        vendor = licenses['response'][0]['Vendor_Name_Lookup']
        vendor_record = crm_obj.get_record('Vendors', vendor['id'])
        if vendor_record['status_code'] == 200:
            response = dict()
            response['vendor'] = vendor_record['response'][vendor['id']]
            response['licenses'] = licenses['response']
            return response
    return {}