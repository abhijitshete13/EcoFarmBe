import json
import base64
from io import (BytesIO, )
from datetime import (datetime, timedelta, )
from core.settings import (
    BOOKS_CLIENT_ID,
    BOOKS_CLIENT_SECRET,
    BOOKS_ORGANIZATION_ID,
    BOOKS_REDIRECT_URI,
    BOOKS_REFRESH_TOKEN,
    ESTIMATE_TAXES,
    TRANSPORTATION_FEES,
)
from brand.models import (Brand, License, LicenseProfile, )
from pyzoho.books import (Books, )
from .models import (Integration, )
from .crm_format import (CRM_FORMAT, )
from .inventory import (get_inventory_items, )
from .sign import (submit_estimate, )


def get_books_obj():
    """
    Get Pyzoho books object.
    """
    try:
        token = Integration.objects.get(name='books')
        access_token = token.access_token
        access_expiry = token.access_expiry
        refresh_token = token.refresh_token
    except Integration.DoesNotExist:
        access_token = access_expiry = None
        refresh_token = BOOKS_REFRESH_TOKEN
    books_obj = Books(
        client_id=BOOKS_CLIENT_ID,
        client_secret=BOOKS_CLIENT_SECRET,
        redirect_uri=BOOKS_REDIRECT_URI,
        organization_id=BOOKS_ORGANIZATION_ID,
        refresh_token=refresh_token,
        access_expiry=access_expiry,
        access_token=access_token)
    if books_obj.refreshed:
        Integration.objects.update_or_create(
            name='books',
            defaults={
                "name":'books',
                "client_id":BOOKS_CLIENT_ID,
                "client_secret":BOOKS_CLIENT_SECRET,
                "refresh_token":books_obj.refresh_token,
                "access_token":books_obj.access_token,
                "access_expiry":books_obj.access_expiry[0]}
    )
    return books_obj

def get_format_dict(module):
    """
    Return Contact-CRM fields dictionary.
    """
    return CRM_FORMAT[module]

def create_customer_in_books(id=None, is_update=False, is_single_user=False, params={}):
    """
    Create customer in the Zoho books.
    """
    response_list = list()
    if is_single_user:
        records = [License.objects.select_related().get(id=id).__dict__]
    else:
        if id:
            records = Brand.objects.filter(id=id)
        else:
            records = Brand.objects.filter(is_updated_in_crm=False)
    for record in records:
        request = dict()
        record_id = record.id
        if not is_single_user:
            request.update(record.__dict__)
            licenses = record.license_set.values()
        else:
            licenses = records
        for license in licenses:
            request.update(license)
            license_db = License.objects.select_related().get(id=license['id'])
            request.update(license_db.license_profile.__dict__)
            try:
                request.update(license_db.profile_contact.profile_contact_details)
            except Exception:
                pass
            if is_update:
                request.update({'id': request['zoho_books_id']})
            books_dict = get_format_dict('Books_Customer')
            try:
                if not is_update:
                    del books_dict['contact_id']
                else:
                    del books_dict['contact_persons']
            except KeyError:
                pass
            record_dict = dict()
            for k,v in books_dict.items():
                if v.endswith('_parse'):
                    v = v.split('_parse')[0]
                    v = parse_books_fields(k, v, request)
                    record_dict[k] = v
                else:
                    v = request.get(v)
                    record_dict[k] = v
            for customer_type in ['vendor', 'customer']:
                record_dict['contact_type'] = customer_type
                if is_update:
                    response = update_contact(record_dict, params=params)
                else:
                    response = create_contact(record_dict, params=params)
                if response.get('contact_id'):
                    try:
                        if is_single_user:
                            record_obj = License.objects.get(id=record_id)
                        else:
                            record_obj = Brand.objects.get(id=record_id)
                        record_obj.zoho_books_id = response.get('contact_id')
                        record_obj.save()
                    except KeyError as exc:
                        print(exc)
                response_list.append(response)
    return response_list

def parse_books_fields(k, v, request):
    """
    Parse books fields.
    """
    value = request.get(v, None)
    if v in ['billing_address', 'mailing_address']:
        return {
            'address': value.get('street'),
            'street2': value.get('street_line_2'),
            'state_code': value.get('state'),
            'city': value.get('city'),
            'state': value.get('state'),
            'zip': value.get('zip_code'),
            'country': value.get('country'),
            'phone': value.get('phone')
        }
    elif v == 'employees':
        contact_persons = list()
        for value in request.get(v, None):
            email = value.get('employee_email')
            is_duplicate = is_duplicate_contact(email, contact_persons)
            if is_duplicate == False:
                contact_persons.append({
                    'first_name': value.get('employee_name'),
                    'last_name': value.get('last_name'),
                    'email': value.get('employee_email'),
                    'phone': value.get('phone'),
                    'mobile': value.get('phone'),
                    'designation': value.get('roles')[0],
                    'department': value.get('department'),
                    # 'is_primary_contact': is_primary,
                    'skype': value.get('skype'),
                })
        return contact_persons
    elif v == 'contact_type':
        if request.get('is_buyer'):
            return 'customer'
        elif request.get('is_seller'):
            return 'vendor'
        
def is_duplicate_contact(email, contact_persons):
    """
    Check if contact is duplicate.
    """
    for contact in contact_persons:
        if email == contact.get('email'):
            return True
    return False

def create_contact(data, params=None):
    """
    Create contact in Zoho Books.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.create_contact(data, parameters=params)

def update_contact(data, params=None):
    """
    Update contact in Zoho Books.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.update_contact(data.get('contact_id'), data, parameters=params)

def get_contact(contact_id, params=None):
    """
    Get contact.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.get_contact(contact_id, parameters=params)

def get_contact_addresses(contact_name):
    """
    Get contact address list.
    """
    obj = get_books_obj()
    contact = get_contact_id(obj, contact_name)
    if contact.get('code'):
        return {'code': '1003', 'error': 'Contact not found in zoho books.'}
    contact_id = contact['contact_id']
    contact_obj = obj.Contacts()
    return contact_obj.get_contact_addresses(contact_id)

def add_contact_address(contact_name, data, params=None):
    """
    Add contact address in Zoho Books.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    contact = get_contact_id(obj, contact_name)
    if contact.get('code'):
        return {'code': '1003', 'error': 'Contact not found in zoho books.'}
    contact_id = contact['contact_id']
    return contact_obj.add_contact_address(contact_id, data, parameters=params)

def edit_contact_address(contact_name, address_id, data, params=None):
    """
    Edit contact address in Zoho Books.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    contact = get_contact_id(obj, contact_name)
    if contact.get('code'):
        return {'code': '1003', 'error': 'Contact not found in zoho books.'}
    contact_id = contact['contact_id']
    return contact_obj.edit_contact_address(contact_id, address_id, data, parameters=params)

def get_contact_person(contact_id, contact_person_id, params=None):
    """
    Get contact person.
    """
    obj = get_books_obj()
    contact_obj = obj.ContactPersons()
    return contact_obj.get_contact_person(contact_id, contact_person_id, parameters=params)

def list_contact_persons(params=None):
    """
    List contact person.
    """
    obj = get_books_obj()
    contact_obj = obj.ContactPersons()
    return contact_obj.list_contact_persons(parameters=params)

def create_contact_person(data, params=None):
    """
    Create contact person.
    """
    obj = get_books_obj()
    contact_obj = obj.ContactPersons()
    return contact_obj.create_contact_person(data, parameters=params)

def update_contact_person(contact_person_id, data, params=None):
    """
    Update contact person.
    """
    obj = get_books_obj()
    contact_obj = obj.ContactPersons()
    return contact_obj.update_contact_person(contact_person_id, data, parameters=params)

def get_item_dict(book, inventory):
    """
    Return Zoho Book item.
    """
    return {
        'item_id': book.get('item_id'),
        'sku': book.get('sku'),
        'name': book.get('name'),
        'rate': inventory.get('rate', book.get('rate')),
        'quantity': inventory.get('quantity'),
        'category_name': inventory.get('category_name'),
        'item_custom_fields': inventory.get('item_custom_fields'),
    }

def get_tax(obj, tax):
    """
    Return tax information.
    """
    tax_obj = obj.Items()
    return tax_obj.list_items(parameters={'name': tax})

def get_tax_rates():
    """
    Get all tax rates.
    """
    try:
        taxes = json.loads(ESTIMATE_TAXES)
    except Exception:
        taxes = ESTIMATE_TAXES
    books_obj = get_books_obj()
    response = dict()
    for k,v in taxes.items():
        item = get_tax(books_obj, v)['response'][0]
        response[item['name']] = item['rate']
    return response

def get_transportation_fees(name=None):
    """
    Return transportation fees.
    """
    obj = get_books_obj()
    if name:
        return get_tax(obj, name)
    return get_tax(obj, TRANSPORTATION_FEES)

def calculate_tax(product_category, quantity):
    """
    Calculate tax from product category for estimate page.
    """
    try:
        taxes = json.loads(ESTIMATE_TAXES)
    except Exception:
        taxes = ESTIMATE_TAXES
    books_obj = get_books_obj()
    if product_category == 'Flower':
        item = get_tax(books_obj, taxes['Flower'])['response'][0]
        item_id = item['item_id']
        item_sku = item['sku']
        item_name = item['name']
        tax = item['rate']
        total_tax = float(quantity) * float(tax)
    elif product_category == 'Trim':
        item = get_tax(books_obj, taxes['Trim'])['response'][0]
        item_name = item['name']
        item_id = item['item_id']
        item_sku = item['sku']
        tax = item['rate']
        total_tax = float(quantity) * float(tax)
    else:
        return {'status_code': 400,
                'error': 'product category not found.'}
    return {
        'status_code': 200,
        'response': {
            'item_name': item_name,
            'total_tax': total_tax,
            'quantity': quantity,
            'item_id': item_id,
            'sku': item_sku,
            'rate': tax
        }
    }

def get_item(obj, data):
    """
    Return item from Zoho books with applied tax.
    """
    try:
        taxes = json.loads(ESTIMATE_TAXES)
    except Exception:
        taxes = ESTIMATE_TAXES
    line_items = list()
    if not data.get('line_items'):
        return {"code": 1004, "data": data}
    for line_item in data.get('line_items'):
        item_obj = obj.Items()
        try:
            book_item = item_obj.list_items(parameters={'search_text': line_item['sku']})
            book_item = book_item['response']
        except KeyError:
            return {"code": 1003, "error": "Customer name not provided"}
        if len(book_item) == 1:
            book_item = book_item[0]
        elif len(book_item) > 1:
            for i in book_item:
                if i['sku'] == line_item['sku']:
                    book_item = i
                    break
        else:
            return {"code": 1003, "message": "Item not in zoho books."}
        item = get_item_dict(book_item, line_item)
        line_items.append(item)
    data['line_items'] = line_items
    return {"code": 0, "data": data}

def get_customer(obj, data):
    """
    Return customer from Zoho books using Zoho Inventory name.
    """
    contact_obj = obj.Contacts()
    try:
        customer = contact_obj.list_contacts(parameters={'contact_name': data['customer_name']})
        customer = customer['response']
    except KeyError:
        return {"code": 1003, "error": "Customer name not provided"}
    if len(customer) == 1:
        customer = customer[0]
    elif len(customer) > 1:
        for i in customer:
            if i['contact_name'] == data['customer_name'] and i['contact_type'] == 'customer':
                customer = i
                break
    else:
        return {"code": 1003, "message": "Contact not in zoho books."}
    if customer.get('email') == '':
        return {"code": 1003, "message": "Contact don't have email associated with it."}
    data['customer_id'] = customer['contact_id']
    return {"code": 0, "data": data}

def create_estimate(data, params=None):
    """
    Create estimate in Zoho Books.
    """
    try:
        obj = get_books_obj()
        estimate_obj = obj.Estimates()
        result = get_customer(obj, data)
        if result['code'] != 0:
            return result
        result = get_item(obj, result['data'])
        if result['code'] != 0:
           return result
        return estimate_obj.create_estimate(result['data'], parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def delete_estimate(estimate_id, params=None):
    """
    Delete an estimate in Zoho Books.
    """
    try:
        obj = get_books_obj()
        estimate_obj = obj.Estimates()
        return estimate_obj.delete_estimate(estimate_id=estimate_id, parameters=params)
    except Exception as exc:
        return {
            "status_code": 400,
            "error": exc
        }

def update_estimate(estimate_id, data, params=None):
    """
    Update an estimate in Zoho Books.
    """
    try:
        obj = get_books_obj()
        estimate_obj = obj.Estimates()
        result = get_customer(obj, data)
        if result['code'] != 0:
            return result
        result = get_item(obj, result['data'])
        if result['code'] != 0 and result['code'] != 1004:
           return result
        return estimate_obj.update_estimate(estimate_id, result['data'], parameters=params)
    except Exception as exc:
        return {
            'status_code': 400,
            'error': exc
        }
        
def get_estimate(estimate_id, params=None):
    """
    Get an estimate.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.get_estimate(estimate_id, parameters=params)

def list_estimates(params=None):
    """
    List estimates.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.list_estimates(parameters=params)

def update_estimate_address(estimate_id, address_type, data, params=None):
    """
    Update estimate address in zoho books.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.update_estimate_address(estimate_id, address_type, data, parameters=params)

def send_estimate_to_sign(estimate_id, customer_name):
    """
    sync estimate status from zoho books.
    """
    try:
        obj = get_books_obj()
        contact = get_contact_id(obj, customer_name)
        if contact.get('code'):
            return {'code': '1003', 'error': 'Contact not found in zoho books.'}
        contact_id = contact['contact_id']
        file_obj = get_estimate(estimate_id=estimate_id, params={'accept': 'pdf'})
        file_name = (file_obj['Content-Disposition'].split(';')[1]).split('=')[1].strip('"')
        file_binary = BytesIO(base64.b64decode(file_obj['data']))
        file_type = 'application/pdf'
        file_obj = [[file_name, file_binary, file_type]]
        if not contact.get('email'):
            return {'code': 1003, 'error': 'Contact doesnot have email in zoho books.'}
        customer_dict = [{'name': contact['contact_name'], 'email': contact['email']}]
        return submit_estimate(
            file_obj=file_obj,
            recipients=customer_dict,
            notes="",
            expiry=10,
            reminder_period=15
            )
    except KeyError as exc:
        print('Key not found', exc)
    except IndexError as exc:
        print('problem with file object', exc)
    except Exception as exc:
        print('error in sync estimate status', exc)

def mark_estimate(estimate_id, status, params=None):
    """
    Mark statement as sent, accepted, declined.
    """
    obj = get_books_obj()
    estimate_obj = obj.Estimates()
    return estimate_obj.mark_as(estimate_id, status, parameters=params)

def list_contacts(params=None):
    """
    List contact.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.list_contacts(parameters=params)

def get_purchase_order(po_id, params=None):
    """
    Get specific purchase order.
    """
    obj = get_books_obj()
    po_obj = obj.PurchaseOrders()
    return po_obj.get_purchase_order(po_id=po_id, parameters=params)

def list_purchase_orders(params=None):
    """
    List specific purchase order.
    """
    obj = get_books_obj()
    po_obj = obj.PurchaseOrders()
    legal_business_name = params.get('vendor_name')
    contact_obj = obj.Contacts()
    contacts = contact_obj.list_contacts({'cf_legal_business_name': legal_business_name})
    for contact in contacts['response']:
        if contact['company_name'] == legal_business_name and contact['contact_type'] == 'vendor':
            params['vendor_name'] = contact['contact_name']
            break
    return po_obj.list_purchase_orders(parameters=params)

def get_vendor_payment(payment_id, params={}):
    """
    Return vendor payments made.
    """
    obj = get_books_obj()
    vp_obj = obj.VendorPayments()
    return vp_obj.get_payment(payment_id=payment_id, parameters=params)

def list_vendor_payments(params=None):
    """
    List vendor payments.
    """
    obj = get_books_obj()
    po_obj = obj.VendorPayments()
    payments = po_obj.list_payments(parameters=params)
    for payment in payments.get('response'):
        data = get_vendor_payment(payment['payment_id'])
        payment['balance'] = 0
        for record in data.get('bills'):
            payment['balance'] += record['balance']
    return payments

def get_customer_payment(payment_id, params={}):
    """
    Return customer payments made.
    """
    obj = get_books_obj()
    vp_obj = obj.CustomerPayments()
    return vp_obj.get_payment(payment_id=payment_id, parameters=params)

def list_customer_payments(params=None):
    """
    List customer payments.
    """
    obj = get_books_obj()
    po_obj = obj.CustomerPayments()
    payments = po_obj.list_payments(parameters=params)
    for payment in payments.get('response'):
        data = get_customer_payment(payment['payment_id'])
        payment['balance'] = 0
        for record in data.get('invoices'):
            payment['balance'] += record['balance']
    return payments

def get_invoice(invoice_id, params=None):
    """
    Get an invoice.
    """
    obj = get_books_obj()
    invoice_obj = obj.Invoices()
    return invoice_obj.get_invoice(invoice_id=invoice_id, parameters=params)

def list_invoices(params=None):
    """
    List invoices.
    """
    obj = get_books_obj()
    invoice_obj = obj.Invoices()
    return invoice_obj.list_invoices(parameters=params)

def get_vendor_credit(credit_id, params=None):
    """
    Get vendor credit.
    """
    obj = get_books_obj()
    invoice_obj = obj.VendorCredits()
    return invoice_obj.get_vendor_credit(credit_id=credit_id, parameters=params)

def list_vendor_credits(params=None):
    """
    List vendor credits.
    """
    obj = get_books_obj()
    invoice_obj = obj.VendorCredits()
    return invoice_obj.list_vendor_credits(parameters=params)

def get_unpaid_bills(vendor, status='unpaid'):
    """
    Return total unpaid bills.
    """
    response = list_bills({
        'vendor_name': vendor,
        'status': status})['response']
    unpaid = sum([i['balance'] for i in response])
    return unpaid

def get_available_credit(vendor, status='open'):
    """
    Get available vendor credits.
    """
    response = list_vendor_credits({
        'vendor_name': vendor,
        'status':status})['response']
    credits = sum([i['total'] for i in response])
    return credits

def get_contact_id(obj, contact_name):
    """
    Get contact id using contact name.
    """
    contact_obj = obj.Contacts()
    try:
        customer = contact_obj.list_contacts(parameters={'contact_name': contact_name})
        customer = customer['response']
    except KeyError:
        return {"code": 1003, "error": "Customer name not provided"}
    if len(customer) == 1:
        customer = customer[0]
    elif len(customer) > 1:
        for i in customer:
            if i['contact_name'] == contact_name:
                customer = i
                break
    else:
        return {"code": 1003, "message": "Contact not in zoho books."}
    return customer

def get_contact_statement(contact_name):
    """
    Get contact address list.
    """
    obj = get_books_obj()
    contact = get_contact_id(obj, contact_name)
    if contact.get('code'):
        return {'code': '1003', 'error': 'Contact not found in zoho books.'}
    contact_id = contact['contact_id']
    contact_obj = obj.Contacts()
    return contact_obj.get_statement(contact_id)

# def create_purchase_order(data, params=None):
#     """
#     Create purchase order in Zoho Books.
#     """
#     obj = get_books_obj()
#     po_obj = obj.PurchaseOrders()
#     result = get_customer(obj, data)
#     if result['code'] != 0:
#         return result
#     result = get_item(obj, result['data'])
#     if result['code'] != 0:
#         return result
#     return po_obj.create_purchase_order(result['data'], parameters=params)

def get_bill(bill_id, params=None):
    """
    Get a bill.
    """
    obj = get_books_obj()
    bill_obj = obj.Bills()
    return bill_obj.get_bill(bill_id=bill_id, parameters=params)

def list_bills(params=None):
    """
    List bills.
    """
    obj = get_books_obj()
    bill_obj = obj.Bills()
    contact_obj = obj.Contacts()
    legal_business_name = params.get('vendor_name')
    contacts = contact_obj.list_contacts({'cf_legal_business_name': legal_business_name})
    for contact in contacts['response']:
        if contact['company_name'] == legal_business_name and contact['contact_type'] == 'vendor':
            params['vendor_name'] = contact['contact_name']
            break
    return bill_obj.list_bills(parameters=params)

def get_salesorder(so_id, params=None):
    """
    Get sales order
    """
    obj = get_books_obj()
    bill_obj = obj.SalesOrders()
    return bill_obj.get_sales_order(so_id=so_id, parameters=params)

def list_salesorders(params=None):
    """
    List sales orders
    """
    obj = get_books_obj()
    bill_obj = obj.SalesOrders()
    return bill_obj.list_sales_orders(parameters=params)
