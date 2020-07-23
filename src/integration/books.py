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
)
from pyzoho.books import (Books, )
from .models import (Integration, )
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
    except Integration.DoesNotExist:
        access_token = access_expiry = None
    books_obj = Books(
        client_id=BOOKS_CLIENT_ID,
        client_secret=BOOKS_CLIENT_SECRET,
        redirect_uri=BOOKS_REDIRECT_URI,
        organization_id=BOOKS_ORGANIZATION_ID,
        refresh_token=BOOKS_REFRESH_TOKEN,
        access_expiry=access_expiry,
        access_token=access_token)
    if books_obj.refreshed:
        Integration.objects.update_or_create(
            name='books',
            defaults={
                "name":'books',
                "client_id":BOOKS_CLIENT_ID,
                "client_secret":BOOKS_CLIENT_SECRET,
                "refresh_token":BOOKS_REFRESH_TOKEN,
                "access_token":books_obj.access_token,
                "access_expiry":books_obj.access_expiry[0]}
    )
    return books_obj
        
def create_contact(data, params=None):
    """
    Create contact in Zoho Books.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.create_contact(data, parameters=params)

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
        'category_name': inventory.get('category_name')
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
        item_name = item['name']
        tax = item['rate']
        total_tax = float(quantity) * float(tax)
    elif product_category == 'Trim':
        item = get_tax(books_obj, taxes['Trim'])['response'][0]
        item_name = item['name']
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
            'quantity': quantity
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
            if i['contact_name'] == data['customer_name']:
                customer = i
                break
    else:
        return {"code": 1003, "message": "Contact not in zoho books."}
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

def sync_estimate_status(response, params=None):
    """
    sync estimate status from zoho books.
    """
    try:
        response = response.split('&')
        response = {i.split('=')[0]:i.split('=')[1] for i in response}
        file_obj = get_estimate(estimate_id=response['estimate_id'], params={'accept': 'pdf'})
        file_name = (file_obj['Content-Disposition'].split(';')[1]).split('=')[1].strip('"')
        file_binary = BytesIO(base64.b64decode(file_obj['data']))
        file_type = 'application/pdf'
        file_obj = [[file_name, file_binary, file_type]]
        obj = get_books_obj()
        customer = get_contact(contact_id=response['customer_id'])
        customer_dict = [{'name': customer['contact_name'], 'email': customer['email']}]
        return submit_estimate(
            file_obj=file_obj,
            # recipients=customer_dict,
            recipients=[{'name': 'harshal', 'email': 'harshal.c@amazatic.com'}],
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
    

def get_contact(contact_id, params=None):
    """
    Get contact.
    """
    obj = get_books_obj()
    contact_obj = obj.Contacts()
    return contact_obj.get_contact(contact_id, parameters=params)

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
    return po_obj.list_purchase_orders(parameters=params)

def get_vendor_payment(payment_id, params=None):
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
    return po_obj.list_payments(parameters=params)

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
    return invoice_obj.list_vendor_credit(parameters=params)

def get_unpaid_invoices(vendor, status='unpaid'):
    """
    Return total unpaid invoices.
    """
    response = list_invoices({
        'customer_name': vendor,
        'status': status})['response']
    unpaid = sum([i['total'] for i in response])
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