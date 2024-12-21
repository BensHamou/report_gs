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
from rest_framework.exceptions import NotAuthenticated
from rest_framework.views import APIView

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
        moves = MoveLine.objects.filter(Q(move__line__in=user.lines.all().values('id')) | Q(move__line__isnull=True, move__site=user.default_site)).order_by('-date_modified')
        paginator = StandardResultsSetPagination()
        paginated_moves = paginator.paginate_queryset(moves, request)
        serializer = MoveLineSerializer(paginated_moves, many=True)
        return paginator.get_paginated_response(serializer.data)
    except NotAuthenticated:
        return Response({'error': 'L\'utilisateur doit être authentifié pour accéder à cette ressource.'}, status=401)
    
class SyncDataView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sites = Site.objects.all()
        warehouses = Warehouse.objects.all()
        emplacements = Emplacement.objects.all()
        lines = Line.objects.all()
        families = Family.objects.all()
        packings = Packing.objects.all()
        products = Product.objects.all()

        data = {
            "sites": SiteSerializer(sites, many=True).data,
            "warehouses": WarehouseSerializer(warehouses, many=True).data,
            "emplacements": EmplacementSerializer(emplacements, many=True).data,
            "lines": LineSerializer(lines, many=True).data,
            "families": FamilySerializer(families, many=True).data,
            "packings": PackingSerializer(packings, many=True).data,
            "products": ProductSerializer(products, many=True).data,
        }

        return Response(data)
    
class ProductAvalibilityView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        site_id = request.data.get('site_id')
        product_ids = request.data.get('product_ids')

        if not site_id or not product_ids:
            return Response({"detail": "Site_id ou product_ids manquant"}, status=400)
        
        products = Product.objects.filter(id__in=product_ids)
        product_data = []

        for product in products:
            stock_details = DisponibilitySerializer(product.state_in_site(site_id), many=True).data
            unit_qte = product.unit_qte(site_id)
            
            product_data.append({'product': ProductSerializer(product).data, 'stock_details': stock_details, 'global_qte': unit_qte})
        return Response(product_data)
    
# class ConfirmMoveOutView(APIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     def post(self, request, *args, **kwargs):
#         move_line = request.data.get('move_id')

#         if not move_line:
#             return Response({"detail": "Sortie ID manquant"}, status=400)
        
#         try:
#             move_line = MoveLine.objects.get(id=move_line)
#             success = move_line.move.changeState(request.user.id, 'Confirmé')
#             if success:
#                 return JsonResponse({'success': True, 'message': 'Entrée confirmé avec succès.', 'move_line_id': move_line_id})
#             return Response({"detail": "Sortie confirmée"}, status=200)
#         except Move.DoesNotExist:
#             return Response({"detail": "Sortie inexistante"}, status=404)
        
#         success = move_line.move.changeState(request.user.id, 'Confirmé')
#         if success:
#             return JsonResponse({'success': True, 'message': 'Entrée confirmé avec succès.', 'move_line_id': move_line_id})
#         else:
#             return JsonResponse({'success': False, 'message': 'Entrée introuvable.'})
        
#         move = MoveLine.objects.get(id=move_line)
#         products = Product.objects.filter(id__in=product_ids)
#         product_data = []

#         for product in products:
#             stock_details = DisponibilitySerializer(product.state_in_site(site_id), many=True).data
#             unit_qte = product.unit_qte(site_id)
            
#             product_data.append({'product': ProductSerializer(product).data, 'stock_details': stock_details, 'global_qte': unit_qte})
#         return Response(product_data)
    
# api_body = {
#     'user_id': 1,
#     'is_transfer': True/False,
#     'transferred_products': [
#         {
#             'product_id': 1,
#             'from': [
#                 {
#                     'emplacement_id': 1,
#                     'qte': 10,
#                     'n_lot': 'lot1'
#                 },
#                 {
#                     'emplacement_id': 2,
#                     'qte': 11,
#                     'n_lot': 'lot2'
#                 },
#             ]
#         },
#         {
#             'product_id': 2,
#             'from': [
#                 {
#                     'emplacement_id': 3,
#                     'qte': 12,
#                     'n_lot': 'lot3'
#                 },
#                 {
#                     'emplacement_id': 4,
#                     'qte': 13,
#                     'n_lot': 'lot4'
#                 },
#             ]
#         }
#     ]
# }

