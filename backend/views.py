from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum,Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Call the models
from .models import Program, Platform, Report

# Create your views here.
def CustomLoginView(request):
    # Check if user is authenticated
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:  # Check if the user is active
                login(request, user)    
                return redirect('home')
            
            else:
                messages.error(request, "Your account is inactive.")
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'auth/index.html')

def CustomLogoutView(request):
    logout(request)
    return redirect('login')

@login_required()
def home(request):
    if request.method == "GET":
        new_reports = Report.objects.filter(status='New').count()
        rewarded_reports = Report.objects.filter(status='Rewarded').count()
        rejected_reports = Report.objects.filter(status__in=['Closed', 'Duplicate']).count()
        triaged_reports = Report.objects.filter(status='Triaged').count()
        total_earned = Report.objects.filter(status='Rewarded').aggregate(Sum('reward'))['reward__sum'] or 0

        return render(request, 'dashboard/home.html', {
            'new_reports': new_reports,
            'rewarded_reports': rewarded_reports,
            'rejected_reports': rejected_reports,
            'triaged_reports': triaged_reports,
            'total_earned': total_earned
        })

@login_required()
def ReportView(request):
    if request.method == "GET":
        daterange = request.GET.get('daterange', '')
        severity = request.GET.get('severity', '')
        status = request.GET.get('status', '')
        program = request.GET.get('program', '')
        platform = request.GET.get('platform', '')

        # Initialize the filters as an empty Q object
        filters = Q()

        # Add conditions to filters based on GET parameters
        if severity:
            filters &= Q(severity=severity)
        if status:
            filters &= Q(status=status)
        if program:
            filters &= Q(program__id=program)
        if platform:
            filters &= Q(program__platform__id=platform)

        # Apply date range filter if provided
        if daterange:
            start_date, end_date = daterange.split(' - ')
            filters &= Q(created_at__range=[start_date, end_date])

        # Filter the reports based on the applied filters
        reports = Report.objects.filter(filters)

        # Get the lists of severities, statuses, programs, and platforms for the dropdowns
        severities =  (
            ('Low', 'Low'),
            ('Medium', 'Medium'),
            ('High', 'High'),
            ('Critical', 'Critical'),
        )
        statuses = (
            ('New', 'New'),
            ('Triaged', 'Triaged'),
            ('Rewarded', 'Rewarded'),
            ('Duplicate', 'Duplicate'),
            ('Closed', 'Closed'),
        )
        programs = Program.objects.all()
        platforms = Platform.objects.all()

        return render(request, 'reports/reports.html', {
            'reports': reports,
            'severities': severities,
            'statuses': statuses,
            'programs': programs,
            'platforms': platforms,
        })
@login_required()
def ReportCreate(request):
    if request.method == "POST":
        title = request.POST.get('title')
        vulnerability = request.POST.get('vulnerability')
        severity = request.POST.get('severity')
        status = request.POST.get('status')
        program = request.POST.get('program')
        reward = request.POST.get('reward')
        
        report = Report(title=title, vulnerability=vulnerability, severity=severity, status=status, program_id=program, reward=reward)
        report.save()
        
        return redirect('reports')
    return redirect('reports')
@login_required()
def ReportEdit(request, id):
    if request.method == "POST":
        report = get_object_or_404(Report, pk=id)
        
        if report:
            report.title = request.POST.get('title')
            report.vulnerability = request.POST.get('vulnerability')
            report.severity = request.POST.get('severity')
            report.status = request.POST.get('status')
            report.program_id = request.POST.get('program')
            report.reward = request.POST.get('reward')
            report.save()

            return redirect('reports')
    return redirect('reports')

@login_required()
def ReportDelete(request, id):
    if request.method == "POST":
        report = get_object_or_404(Report, pk=id)
        
        if report:
            report.delete()
            
            return redirect('reports')
    return redirect('reports')
@login_required()
def ProgramView(request):
    if request.method == "GET":
        programs = Program.objects.all().order_by('-created_at')
        platforms = Platform.objects.all()
        paginator = Paginator(programs, 10)  # 10 devices per page
        
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'programs/programs.html', {
            'programs': page_obj,
            'platforms': platforms
        })
@login_required()
def ProgramCreate(request):
    if request.method == "POST":
        name = request.POST.get('name')
        platform = request.POST.get('platform')
        program = Program(name=name, platform_id=platform)
        program.save()
        
        return redirect('programs')
    return redirect('programs')
@login_required()
def ProgramEdit(request, id):
    if request.method == "POST":
        program = get_object_or_404(Program, pk=id)
        
        if program:
            program.name = request.POST.get('name')
            program.platform_id = request.POST.get('platform')
            program.save()

            return redirect('programs')
    return redirect('programs')
@login_required()
def ProgramDelete(request, id):
    if request.method == "POST":
        program = get_object_or_404(Program, pk=id)
        
        if program:
            program.delete()
            
            return redirect('programs')
    return redirect('programs')

def PlatformView(request):
    if request.method == "GET":
        platforms = Platform.objects.all().order_by('-created_at')
        paginator = Paginator(platforms, 10)  # 10 devices per page
        
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'platforms/platforms.html', {
            'platforms': page_obj
        })
@login_required()
def PlatformCreate(request):
    if request.method == "POST":
        name = request.POST.get('name')
        platform = Platform(name=name)
        platform.save()
        
        return redirect('platforms')
    return redirect('platforms')
@login_required()
def PlatformEdit(request, id):
    if request.method == "POST":
        platform = get_object_or_404(Platform, pk=id)
        
        if platform:
            platform.name = request.POST.get('name')
            platform.save()

            return redirect('platforms')
    return redirect('platforms')
@login_required()
def PlatformDelete(request, id):
    if request.method == "POST":
        platform = get_object_or_404(Platform, pk=id)
        
        if platform:
            platform.delete()
            
            return redirect('platforms')
    return redirect('platforms')
