from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import *
import json
from report.models import *
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import NotAuthenticated, NotFound
from rest_framework import generics
from rest_framework.views import APIView
from django.db.models import Sum

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'success': False, 'message': 'Nom d\'utilisateur et mot de passe requis.'}, status=400)

            user = authenticate(request, username=username, password=password)

            if user is not None:
                token, _ = Token.objects.get_or_create(user=user)
                return JsonResponse({'success': True, 'token': token.key, 'fullname': user.fullname, 'default_site': user.default_site.id}, status=200)
            else:
                return JsonResponse({'success': False, 'message': 'Identifiants invalides.'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Données JSON invalides.'}, status=400)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def move_list_api(request):
    try:
        user = request.user
        moves = MoveLine.objects.filter(move__line__in=user.lines.all().values('id')).order_by('-date_modified')
        paginator = StandardResultsSetPagination()
        paginated_moves = paginator.paginate_queryset(moves, request)
        serializer = MoveLineSerializer(paginated_moves, many=True)
        return paginator.get_paginated_response(serializer.data)
    except NotAuthenticated:
        return Response({'error': 'User must be authenticated to access this resource.'}, status=401)
    
class SyncDataView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sites = Site.objects.all()
        warehouses = Warehouse.objects.all()
        zones = Zone.objects.all()
        lines = Line.objects.all()
        families = Family.objects.all()
        units = Unit.objects.all()
        products = Product.objects.all()

        data = {
            "sites": SiteSerializer(sites, many=True).data,
            "warehouses": WarehouseSerializer(warehouses, many=True).data,
            "zones": ZoneSerializer(zones, many=True).data,
            "lines": LineSerializer(lines, many=True).data,
            "families": FamilySerializer(families, many=True).data,
            "units": UnitSerializer(units, many=True).data,
            "products": ProductSerializer(products, many=True).data,
        }

        return Response(data)
    
class MoveOutDetailsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        site_id = request.data.get('site_id')
        product_ids = request.data.get('product_ids')

        if not site_id or not product_ids:
            return Response({"detail": "Missing 'site_id' or 'product_ids'"}, status=400)

        products = Product.objects.filter(id__in=product_ids)
        product_data = []

        for product in products:
            stock_details = product.get_stock_details(site_id)
            
            product_data.append({
                'product_id': product.id,
                'name': product.designation,
                'qte_in_line': stock_details['net_stock'],
                'availability': stock_details['availability'],
                'qte_per_pal': product.qte_per_pal,
                'image': product.image.url if product.image else None,
            })

        return Response(product_data)