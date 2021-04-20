from django.shortcuts import render
from rest_framework import (status,)
from rest_framework.permissions import (AllowAny, IsAuthenticated,)
from rest_framework.response import Response
from rest_framework.views import APIView

from bill.models import (Estimate, LineItem, )
from bill.utils import (parse_fields, )
from integration.books import (create_estimate, delete_estimate,)
from bill.tasks import (notify_estimate)

class EstimateWebappView(APIView):
    """
    View class for Web app estimates.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        """
        Get all estimates from db.
        """
        customer_name = request.query_params.get('customer_name')
        estimate_id = request.query_params.get('estimate_id')
        db_id = kwargs.get('id')
        if customer_name:
            data = Estimate.objects.filter(customer_name=customer_name)
        elif estimate_id:
            data = Estimate.objects.filter(estimate_id=estimate_id)
        elif db_id:
            data = Estimate.objects.filter(id=db_id)
        if data:
            return Response(data.values())
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request):
        """
        Create and estimate in Zoho Books.
        """
        estimate = request.data
        line_items = request.data.get('line_items')
        del estimate['line_items']
        estimate_obj = Estimate.objects.create(**estimate)
        items = list()
        for item in line_items:
            item['estimate'] = estimate_obj
            items.append(LineItem(**item))
        items_obj = LineItem.objects.bulk_create(items)
        if not estimate_obj or not items_obj:
            return Response({'error': 'error while creating estimate'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Success', 'id': estimate_obj.id})

    def put(self, request, **kwargs):
        """
        Update an estimate in Zoho Books.
        """
        id = kwargs.get('id', None)
        is_draft = request.query_params.get('is_draft')
        notification_methods = request.query_params.get('notification_methods')
        if is_draft == 'true' or is_draft == 'True':
            estimate = request.data
            line_items = request.data.get('line_items')
            del estimate['line_items']
            estimate_obj = Estimate.objects.filter(id=id).update(**estimate)
            items = list()
            for item in line_items:
                item_obj = LineItem.objects.filter(estimate_id=id, item_id=item.get('item_id')).update(**item)
            if not estimate_obj:
                return Response({'error': 'error while creating estimate'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': 'Updated', 'id': id})
        else:
            # notify_estimate.delay(notification_methods)
            response = create_estimate(data=request.data, params=request.query_params.dict())
            response = parse_fields('estimate', response)
            if response.get('code') and response.get('code') != 0:
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            estimate = response
            line_items = request.data.get('line_items')
            line_items = parse_fields('item', line_items, many=True)
            estimate_obj = Estimate.objects.filter(id=id).update(**estimate)
            items = list()
            for item in line_items:
                item_obj = LineItem.objects.filter(estimate_id=id, item_id=item.get('item_id')).update(**item)
            return Response({'message': 'Updated', 'id': id})
        return Response({}, status=status.HTTP_400_BAD_REQUEST)