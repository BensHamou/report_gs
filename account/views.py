from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.defaulttags import register
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.contrib import messages 
from .filters import *
from .models import *
from .forms import *
import requests
import json
import uuid

# DECORATORS

@register.filter
def startwith(value, word):
    return str(value).startswith(word)

@register.filter
def is_login(messages):
    for message in messages:
        if str(message).startswith('LOGIN'):
            return True
    return False

@register.filter
def loginerror(value, word):
    return str(value)[len(word):]

def login_success(request):
    return redirect("home")

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'Admin' or request.user.is_admin:
            return view_func(request, *args, **kwargs)
        else:
            return render(request, '403.html', status=403)
    return wrapper

def admin_only_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'Admin':
            return view_func(request, *args, **kwargs)
        else:
            return render(request, '403.html', status=403)
    return wrapper

def page_not_found(request, exception):
    return render(request, '404.html', status=404)

@login_required(login_url='login')
@admin_only_required
def homeView(request):
    context = { 'content': 'content' }
    return render(request, 'home.html', context)

# REDIRECTION
def getRedirectionURL(request, url_path):
    params = {
        'page': request.GET.get('page', '1'),
        'page_size': request.GET.get('page_size', '12'),
        'search': request.GET.get('search', ''),
        'state': request.GET.get('state', ''),
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'site': request.GET.get('site', ''),
        'distru': request.GET.get('distru', '')
    }
    cache_param = str(uuid.uuid4())
    query_string = '&'.join([f'{key}={value}' for key, value in params.items() if value])
    return f'{url_path}?cache={cache_param}&{query_string}'

# USERS

@login_required(login_url='login')
@admin_only_required
def listNewUserView(request):
    users = User.objects.filter(role='Nouveau').order_by('-date_created')
    filteredData = UserFilter(request.GET, queryset=users)
    users = filteredData.qs
    paginator = Paginator(users, 10) 
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = { 'page': page, 'users': filteredData }
    return render(request, 'users_list.html', context)

@login_required(login_url='login')
@admin_only_required
def refreshUserList(request):
    usernames = User.objects.values_list('username', flat=True)
    API_Users = 'https://api.ldap.groupe-hasnaoui.com/get/users?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJUb2tlbiI6IkZvciBEU0kiLCJVc2VybmFtZSI6ImFjaG91cl9hciJ9.aMy1LUzKa6StDvQUX54pIvmjRwu85Fd88o-ldQhyWnE'
    GROUP_Users = 'https://api.ldap.groupe-hasnaoui.com/get/users/group/PUMA-LABS?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJUb2tlbiI6IkZvciBEU0kiLCJVc2VybmFtZSI6ImFjaG91cl9hciJ9.aMy1LUzKa6StDvQUX54pIvmjRwu85Fd88o-ldQhyWnE'
    response = requests.get(API_Users)
    response_ = requests.get(GROUP_Users)
    if response.status_code == 200 and response_.status_code == 200:
        data = json.loads(response.content)
        group_users = json.loads(response_.content)['members']
        new_users_list = [user for user in data['users'] if user['fullname'] in group_users and user['AD2000'] not in usernames]
        for user in new_users_list:
            user = User(username= user['AD2000'], password='password', fullname=user['fullname'], role='Nouveau', is_admin=False, first_name= user['fname'], email= user['mail'], last_name = user['lname'])
            user.save()
    else:
        print('Error: could not fetch data from API')
    cache_param = str(uuid.uuid4())
    url_path = reverse('new_users')
    redirect_url = f'{url_path}?cache={cache_param}'
    return redirect(redirect_url)

@login_required(login_url='login')
@admin_only_required
def editUserView(request, id):
    user = User.objects.get(id=id)
    selectedLines = [line.id for line in user.lines.all()]
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('users')
            return redirect(getRedirectionURL(request, url_path))
    context = {'form': form, 'user_': user, 'selectedLines': selectedLines}
    return render(request, 'edit_user.html', context)

@login_required(login_url='login')
@admin_only_required
def deleteUserView(request, id):
    user = User.objects.get(id=id)
    user.delete()
    url_path = reverse('users')
    return redirect(getRedirectionURL(request, url_path))

@login_required(login_url='login')
@admin_only_required
def listUserView(request):
    users = User.objects.exclude(role='Nouveau').exclude(username='admin').order_by('-date_modified')
    filteredData = UserFilter(request.GET, queryset=users)
    users = filteredData.qs
    selectedUsines = request.GET.getlist('usine')

    if len(selectedUsines) > 0:
        users = users.filter(usines__in=selectedUsines)

    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'page': page, 'filtredData': filteredData, 'selectedUsines': selectedUsines,
    }
    return render(request, 'users_list.html', context)

@login_required(login_url='login')
@admin_only_required
def userProfileView(request, id):
  user = User.objects.get(id=id)
  context = {
    'user_details': user,
  }
  return render(request, 'user_details.html', context)


# AUTHENTIFICATION

class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = CustomLoginForm
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('home'))
        return super().dispatch(request, *args, **kwargs)

def logoutView(request):
    logout(request)
    return redirect('login')

# SITES

@login_required(login_url='login')
@admin_required
def listSiteView(request):
    sites = Site.objects.all().order_by('-date_modified')
    filtered_data = SiteFilter(request.GET, queryset=sites)
    sites = filtered_data.qs
    paginator = Paginator(sites, request.GET.get('page_size', 12))
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'sites': sites}
    return render(request, 'list_sites.html', context)

@login_required(login_url='login')
@admin_required
def deleteSiteView(request, id):
    site = get_object_or_404(Site, id=id)
    try:
        site.delete()
        url_path = reverse('sites')
        return redirect(getRedirectionURL(request, url_path))
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du site: {e}")
        return redirect(getRedirectionURL(request, reverse('sites')))

@login_required(login_url='login')
@admin_required
def createSiteView(request):
    form = SiteForm()
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('sites')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    context = {'form': form}
    return render(request, 'site_form.html', context)

@login_required(login_url='login')
@admin_required
def editSiteView(request, id):
    site = get_object_or_404(Site, id=id)
    form = SiteForm(instance=site)
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('sites')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    context = {'form': form, 'site': site}
    return render(request, 'site_form.html', context)

# LINES

@login_required(login_url='login')
@admin_required
def listLineView(request):
    lines = Line.objects.all().order_by('-date_modified')
    filteredData = LineFilter(request.GET, queryset=lines)
    lines = filteredData.qs
    paginator = Paginator(lines, request.GET.get('page_size', 12))
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'list_lines.html', context)

@login_required(login_url='login')
@admin_required
def deleteLineView(request, id):
    line = get_object_or_404(Line, id=id)
    try:
        line.delete()
        url_path = reverse('lines')
        return redirect(getRedirectionURL(request, url_path))
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression de la ligne : {e}")
        return redirect(getRedirectionURL(request, reverse('lines')))

@login_required(login_url='login')
@admin_required
def createLineView(request):
    form = LineForm()
    if request.method == 'POST':
        form = LineForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('lines')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'selectedShifts': []}
    return render(request, 'line_form.html', context)

@login_required(login_url='login')
@admin_required
def editLineView(request, id):
    line = get_object_or_404(Line, id=id)
    form = LineForm(instance=line)
    selectedShifts = [shift.id for shift in line.shifts.all()]
    if request.method == 'POST':
        form = LineForm(request.POST, instance=line)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('lines')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'line': line, 'selectedShifts': selectedShifts}
    return render(request, 'line_form.html', context)

# ZONES

@login_required(login_url='login')
@admin_required
def listZoneView(request):
    zones = Zone.objects.all().order_by('-date_modified')
    filteredData = ZoneFilter(request.GET, queryset=zones)
    zones = filteredData.qs
    paginator = Paginator(zones, request.GET.get('page_size', 12))
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'list_zones.html', context)

@login_required(login_url='login')
@admin_required
def deleteZoneView(request, id):
    zone = get_object_or_404(Zone, id=id)
    try:
        zone.delete()
        url_path = reverse('zones')
        return redirect(getRedirectionURL(request, url_path))
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression de la zone : {e}")
        return redirect(getRedirectionURL(request, reverse('zones')))

@login_required(login_url='login')
@admin_required
def createZoneView(request):
    form = ZoneForm()
    
    if request.method == 'POST':
        form = ZoneForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('zones')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form}
    return render(request, 'zone_form.html', context)

@login_required(login_url='login')
@admin_required
def editZoneView(request, id):
    zone = get_object_or_404(Zone, id=id)
    form = ZoneForm(instance=zone)
    
    if request.method == 'POST':
        form = ZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('zones')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'zone': zone}
    return render(request, 'zone_form.html', context)

# SHIFT

@login_required(login_url='login')
@admin_required
def listShiftView(request):
    shifts = Shift.objects.all().order_by('-date_modified')
    filteredData = ShiftFilter(request.GET, queryset=shifts)
    shifts = filteredData.qs
    paginator = Paginator(shifts, request.GET.get('page_size', 12))
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'list_shifts.html', context)

@login_required(login_url='login')
@admin_required
def deleteShiftView(request, id):
    shift = get_object_or_404(Shift, id=id)
    try:
        shift.delete()
        url_path = reverse('shifts')
        return redirect(getRedirectionURL(request, url_path))
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du shift : {e}")
        return redirect(getRedirectionURL(request, reverse('shifts')))

@login_required(login_url='login')
@admin_required
def createShiftView(request):
    form = ShiftForm()
    
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('shifts')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form}
    return render(request, 'shift_form.html', context)

@login_required(login_url='login')
@admin_required
def editShiftView(request, id):
    shift = get_object_or_404(Shift, id=id)
    form = ShiftForm(instance=shift)
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('shifts')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'shift': shift}
    return render(request, 'shift_form.html', context)

# WAREHOUSE

@login_required(login_url='login')
@admin_required
def listWarehouseView(request):
    warehouses = Warehouse.objects.all().order_by('-date_modified')
    filteredData = WarehouseFilter(request.GET, queryset=warehouses)
    warehouses = filteredData.qs
    paginator = Paginator(warehouses, request.GET.get('page_size', 12))
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'list_warehouses.html', context)

@login_required(login_url='login')
@admin_required
def deleteWarehouseView(request, id):
    warehouse = get_object_or_404(Warehouse, id=id)
    try:
        warehouse.delete()
        url_path = reverse('warehouses')
        return redirect(getRedirectionURL(request, url_path))
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression de l'entrepôt : {e}")
        return redirect(getRedirectionURL(request, reverse('warehouses')))

@login_required(login_url='login')
@admin_required
def createWarehouseView(request):
    form = WarehouseForm()
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('warehouses')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form}
    return render(request, 'warehouse_form.html', context)

@login_required(login_url='login')
@admin_required
def editWarehouseView(request, id):
    warehouse = get_object_or_404(Warehouse, id=id)
    form = WarehouseForm(instance=warehouse)
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save(user=request.user)
            url_path = reverse('warehouses')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'warehouse': warehouse}
    return render(request, 'warehouse_form.html', context)
