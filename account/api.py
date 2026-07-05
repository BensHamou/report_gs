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
from rest_framework.views import APIView
from django.db import transaction
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


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
                return JsonResponse({'success': True, 'token': token.key, 'fullname': user.fullname, 
                                     'default_site': user.default_site.id, 'role': user.role, 
                                     'allow_policy': user.allow_policy}, status=200)
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
def get_available_palettes_api(request, move_id):
    try:
        move = Move.objects.get(id=move_id)
        if move.state != 'Brouillon':
            return Response({'success': False, 'message': "Le mouvement n'est pas au statut Brouillon."}, status=400)
            
        is_transfer = move.is_transfer
        is_isolation = move.is_isolation
        
        if is_isolation:
            m_type = 'consumption'
        elif is_transfer:
            m_type = 'transfer'
        else:
            m_type = 'normal'

        product_ids = move.move_lines.values_list('product_id', flat=True)
        dispos = Disponibility.objects.filter(
            product_id__in=product_ids,
            emplacement__warehouse__site=move.site,
            qte__gt=0
        ).select_related('emplacement', 'emplacement__warehouse', 'product')

        if m_type == 'normal':
            dispos = dispos.filter(emplacement__quarantine=False, emplacement__temp=False).order_by('expiry_date', 'n_lot')
        elif m_type == 'isolation':
            dispos = dispos.filter(emplacement__quarantine=False)
        elif m_type == 'consumption':
            dispos = dispos.filter(emplacement__quarantine=True)
        elif m_type == 'transfer':
            dispos = dispos.filter(emplacement__quarantine=False, emplacement__temp=False).order_by('expiry_date', 'n_lot')

        scanned_codes = set()
        scanned_detail_codes = DetailCode.objects.filter(line_detail__move_line__move=move).select_related('line_detail', 'line_detail__move_line__product')
        scanned_palettes = []
        for dc in scanned_detail_codes:
            scanned_codes.add(dc.code)
            scanned_palettes.append({
                'id': dc.id,
                'code': dc.code,
                'qte': dc.qte,
                'product_id': dc.line_detail.move_line.product.id,
                'emplacement_id': dc.line_detail.emplacement.id if dc.line_detail.emplacement else None,
                'n_lot': dc.line_detail.n_lot,
                'sequence': dc.sequence
            })

        stock_list = []
        for d in dispos:
            palettes = []
            for line in d.sorted_lines:
                if line.status == 'Valide' and line.code not in scanned_codes:
                    palettes.append({
                        'id': line.id,
                        'code': line.code,
                        'qte': line.qte,
                        'sequence': line.sequence
                    })
            
            if palettes:
                stock_list.append({
                    'product_id': d.product.id,
                    'product_name': d.product.designation,
                    'emplacement_id': d.emplacement.id,
                    'warehouse_id': d.emplacement.warehouse.id,
                    'emplacement_name': f"{d.emplacement.warehouse.designation} - {d.emplacement.designation}",
                    'n_lot': d.n_lot,
                    'qte': d.qte,
                    'palette': d.palette,
                    'expiry_date': d.expiry_date.strftime('%Y-%m-%d') if d.expiry_date else None,
                    'palettes': palettes
                })
        
        move_lines = []
        for ml in move.move_lines.all():
            move_lines.append({
                'product_id': ml.product.id,
                'product_name': ml.product.designation,
                'expected_qte': ml.initial_qte or 0,
            })

        return Response({
            'success': True, 
            'move_lines': move_lines,
            'scanned_palettes': scanned_palettes,
            'available_palettes': stock_list
        }, status=200)

    except Move.DoesNotExist:
        return Response({'success': False, 'message': 'Mouvement introuvable.'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': f'Erreur: {str(e)}'}, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def sync_move_out_scans_api(request, move_id):
    try:
        move = Move.objects.get(id=move_id)
        if move.state != 'Brouillon':
            return Response({'success': False, 'message': "Mouvement n'est pas au statut Brouillon."}, status=400)

        data = request.data
        scans = data.get('scans', [])
        deleted = data.get('deleted', [])

        with transaction.atomic():
            if deleted:
                dcs = DetailCode.objects.filter(
                    line_detail__move_line__move=move,
                    id__in=deleted
                )
                line_details = set(dc.line_detail for dc in dcs)
                dcs.delete()
                
                for ld in line_details:
                    total = ld.detail_codes.aggregate(total=models.Sum('qte'))['total'] or 0
                    pal = ld.detail_codes.count()
                    if pal == 0:
                        ld.delete()
                    else:
                        ld.qte = total
                        ld.palette = pal
                        ld.save()

            for scan in scans:
                code = scan.get('code')
                qte = float(scan.get('qte', 0))
                product_id = scan.get('product_id')
                emplacement_id = scan.get('emplacement_id')
                n_lot = scan.get('n_lot', '/')
                
                if not code or not product_id or not emplacement_id:
                    continue

                move_line = move.move_lines.filter(product_id=product_id).first()
                if not move_line:
                    continue

                product = move_line.product
                if product.qte_per_pal and qte > product.qte_per_pal:
                    transaction.set_rollback(True)
                    return Response({'success': False, 'message': f"La quantité ({qte}) dépasse la limite de {product.qte_per_pal} par palette pour le code {code}."}, status=400)
                
                if product.qte_per_cond:
                    remainder = qte % product.qte_per_cond
                    if remainder > 1e-5 and (product.qte_per_cond - remainder) > 1e-5:
                        transaction.set_rollback(True)
                        return Response({'success': False, 'message': f"La quantité ({qte}) n'est pas un multiple de {product.qte_per_cond} pour le code {code}."}, status=400)

                emp = Emplacement.objects.get(id=emplacement_id)
                
                ld, created = LineDetail.objects.get_or_create(
                    move_line=move_line,
                    emplacement_id=emplacement_id,
                    n_lot=n_lot,
                    defaults={
                        'warehouse_id': emp.warehouse_id,
                        'qte': 0,
                        'palette': 0,
                        'create_uid': request.user,
                        'write_uid': request.user,
                    }
                )

                dc, dc_created = DetailCode.objects.get_or_create(
                    line_detail=ld,
                    code=code,
                    defaults={'qte': qte, 'palette': 1, 'is_scanned': True}
                )

                if not dc_created:
                    dc.qte = qte
                    dc.is_scanned = True
                    dc.save()

                total = ld.detail_codes.aggregate(total=models.Sum('qte'))['total'] or 0
                pal = ld.detail_codes.count()
                ld.qte = total
                ld.palette = pal
                ld.save()

            for ml in move.move_lines.all():
                total_scanned = ml.details.aggregate(total=models.Sum('qte'))['total'] or 0
                if ml.initial_qte and total_scanned > ml.initial_qte:
                    transaction.set_rollback(True)
                    return Response({'success': False, 'message': f"La quantité totale scannée ({total_scanned}) dépasse la quantité attendue ({ml.initial_qte}) pour le produit {ml.product.designation}."}, status=400)

        return Response({'success': True, 'message': 'Synchronisation réussie.'}, status=200)

    except Move.DoesNotExist:
        return Response({'success': False, 'message': 'Mouvement introuvable.'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': f'Erreur: {str(e)}'}, status=500)

class SendWarningEmail(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            subject = f'Tente de scan incorrecte'
            html_message = render_to_string('warning.html', {'user': request.user})
            addresses = request.user.default_site.email.split('&')
            if not addresses:
                addresses = ['mohammed.senoussaoui@grupopuma-dz.com']
            email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
            email.attach_alternative(html_message, "text/html") 
            email.send()
            return Response({"detail": "Mail envoyé avec succès."}, status=200)
        except Exception as e:
            print(e)
            return Response({"detail": f"Erreur interne du serveur - {e}."}, status=500)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def draft_move_list_api(request):
    user = request.user
    if user.role == 'Admin':
        moves = Move.objects.filter(state='Brouillon', type='Sortie')
    else:
        if not user.default_site:
            return Response({"detail": "L'utilisateur n'a pas de site par défaut défini."}, status=400)
        moves = Move.objects.filter(state='Brouillon', type='Sortie', site=user.default_site)
    moves = moves.order_by('-date_modified')
    paginator = StandardResultsSetPagination()
    paginated_moves = paginator.paginate_queryset(moves, request)
    serializer = LightMoveSerializer(paginated_moves, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)
