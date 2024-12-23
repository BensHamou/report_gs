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
from django.db import transaction
from datetime import datetime

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
                return JsonResponse({'success': True, 'token': token.key, 'fullname': user.fullname, 'default_site': user.default_site.id, 'role': user.role}, status=200)
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
        moves = Move.objects.filter(Q(line__in=user.lines.all().values('id')) | Q(line__isnull=True, site=user.default_site)).order_by('-date_modified')
        paginator = StandardResultsSetPagination()
        paginated_moves = paginator.paginate_queryset(moves, request)
        serializer = MoveSerializer(paginated_moves, many=True)
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
        is_transfer = request.data.get('is_transfer', False)

        if not site_id or not product_ids:
            return Response({"detail": "Site_id ou product_ids manquant"}, status=400)
        
        products = Product.objects.filter(id__in=product_ids)
        product_data = []

        for product in products:
            stock_details = DisponibilitySerializer(product.state_in_site(site_id), many=True).data
            if is_transfer:
                stock_details = sorted(stock_details, key=lambda x: datetime.strptime(x['production_date'], '%Y-%m-%d'))
            unit_qte = product.unit_qte(site_id)
            
            product_data.append({'product': ProductSerializer(product).data, 'stock_details': stock_details, 'global_qte': unit_qte})
        return Response(product_data)

class CreateMoveOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        is_transfer = request.data.get('is_transfer', False)
        transfer_to = request.data.get('transfer_to', None)
        transferred_products = request.data.get('transferred_products', [])
        n_bls = request.data.get('n_bls', [])

        if not user_id:
            return Response({"detail": "User ID manquant"}, status=400)
        if not transferred_products:
            return Response({"detail": "Produits manquants"}, status=400)
        
        if is_transfer and not transfer_to:
            return Response({"detail": "Site de transfert manquant"}, status=400)

        try:
            user = User.objects.get(id=user_id)
            move = Move.objects.create(site=user.default_site, transfer_to_id=transfer_to, gestionaire=user, type='Sortie', 
                                       is_transfer=is_transfer, state='Brouillon', date=timezone.now(), create_uid=user, write_uid=user)

            for product_data in transferred_products:
                product_id = product_data.get('product_id')
                from_emplacements = product_data.get('from', [])
                product = Product.objects.get(id=product_id)

                move_line = MoveLine.objects.create(move=move, product=product, lot_number='/', create_uid=user, write_uid=user, lost_qte=0)
                
                for from_data in from_emplacements:
                    emplacement_id = from_data.get('emplacement_id')
                    qte = from_data.get('qte')
                    n_lot = from_data.get('n_lot')
                    emplacement = Emplacement.objects.get(id=emplacement_id)
                    LineDetail.objects.create(move_line=move_line, warehouse=emplacement.warehouse, 
                                              emplacement=emplacement, qte=qte, n_lot=n_lot, create_uid=user, write_uid=user)

            for bl_data in n_bls:
                numero = bl_data.get('numero')
                is_annexe = bl_data.get('is_annexe', False)
                if not numero:
                    raise ValueError("Numéro BL manquant")
                MoveBL.objects.create(move=move, numero=numero, is_annexe=is_annexe)
            return Response({"detail": "Mouvement créé avec succès", "move_id": move.id}, status=201)
       
        except User.DoesNotExist:
            return Response({"detail": "Utilisateur introuvable"}, status=404)
        except Product.DoesNotExist:
            move.delete()
            return Response({"detail": f"Produit introuvable (ID: {product_id})"}, status=400)
        except Emplacement.DoesNotExist:
            move.delete()
            return Response({"detail": f"Emplacement introuvable (ID: {emplacement_id})"}, status=400)
        except Exception as e:
            move.delete()
            return Response({"detail": f"Erreur lors de la création de mouvement - {e}"}, status=400)
        except ValueError as e:
            move.delete()
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            move.delete()
            return Response({"detail": f"Erreur interne du serveur - {e}"}, status=500)

class ConfirmMoveOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        move_id = request.data.get('move_id')
        if not move_id:
            return Response({"detail": "Movement ID manquant."}, status=400)
        try:
            move = Move.objects.get(id=move_id)
            if move.is_transfer and move.type == 'Entré':
                move.check_can_confirm_transfer()
            success = move.changeState(request.user.id, 'Confirmé')
            if not success:
                return Response({"detail": "Erreur lors de la confirmation du movement."}, status=400)
            return Response({"detail": "Movement confirmée avec succès."}, status=200)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except MoveLine.DoesNotExist:
            return Response({"detail": "Movement introuvable."}, status=404)

class CancelMoveOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        move_id = request.data.get('move_id')

        if not move_id:
            return Response({"detail": "Movement ID manquant."}, status=400)

        try:
            move = Move.objects.get(id=move_id)
            success = move.changeState(request.user.id, 'Annulé')
            if not success:
                return Response({"detail": "Erreur lors de l'annulation du movement."}, status=400)
            return Response({"detail": "Movement annulé avec succès."}, status=200)
        except MoveLine.DoesNotExist:
            return Response({"detail": "Movement introuvable."}, status=404)
        
class DeleteMoveOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        move_id = request.data.get('move_id')

        if not move_id:
            return Response({"detail": "Movement ID manquant."}, status=400)

        try:
            move = Move.objects.get(id=move_id)
            if move.state == 'Brouillon':
                move.delete()
                return Response({"detail": "Movement supprimé avec succès."}, status=200)
            else:
                return Response({"detail": "Impossible de supprimer un movement confirmé."}, status=400)
        except MoveLine.DoesNotExist:
            return Response({"detail": "Movement introuvable."}, status=404)

class ValidateMoveOut(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        move_id = request.data.get('move_id')
        if not move_id:
            return Response({"detail": "Movement ID manquant."}, status=400)
        try:
            move = Move.objects.get(id=move_id)
            # move.can_validate()
            move.do_after_validation(user=request.user)
            if not move.changeState(request.user.id, 'Validé'):
                return Response({"detail": "Échec de la validation de l'état."}, status=400)

            return Response({"detail": "Movement validée avec succès."}, status=200)
        except MoveLine.DoesNotExist:
            return Response({"detail": "Movement introuvable."}, status=404)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        except RuntimeError as e:
            return Response({"detail": str(e)}, status=400)
        except Exception as e:
            return Response({"detail": "Erreur interne du serveur."}, status=500)
        

