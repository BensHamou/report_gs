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
                return JsonResponse({'success': True, 'token': token.key}, status=200)
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
    
class FamilyListView(generics.ListAPIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        family_id = self.kwargs['family_id']
        try:
            family = Family.objects.get(id=family_id)
        except Family.DoesNotExist:
            raise NotFound(detail="Family not found")
        
        return Product.objects.filter(family=family)
    
class MoveOutDetailsView(APIView):
    def post(self, request, *args, **kwargs):
        line_id = request.data.get('line_id')
        product_ids = request.data.get('product_ids')

        if not line_id or not product_ids:
            return Response({"detail": "Missing 'line_id' or 'product_ids'"}, status=400)
        
        try:
            line = Line.objects.get(id=line_id)
            site = line.site
        except Line.DoesNotExist:
            return Response({"detail": "Invalid 'line_id'"}, status=404)

        products = Product.objects.filter(id__in=product_ids)
        product_data = []

        for product in products:
            stock_details = product.get_stock_details(site)
            
            product_data.append({
                'product_id': product.id,
                'name': product.designation,
                'qte_in_line': stock_details['net_stock'],
                'availability': stock_details['availability'],
                'qte_per_pal': product.qte_per_pal,
                'image': product.image.url if product.image else None,
            })

        return Response(product_data)