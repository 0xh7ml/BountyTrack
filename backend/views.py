from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .resources import ProgramResource, ReportResource
from tablib import Dataset
from django.http import JsonResponse

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
                messages.success(request, "You have successfully logged in.")
                return redirect('home')
            
            else:
                messages.error(request, "Your account is inactive.")
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'auth/index.html')

def CustomLogoutView(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('login')

@login_required()
def home(request):
    if request.method == "GET":
        programs = Program.objects.all()
        total_earned = Report.objects.filter(status='Rewarded').aggregate(Sum('reward'))['reward__sum'] or 0
        total_report = Report.objects.all().count()
        
        # Severity counts
        severity_counts = {
            'Low': Report.objects.filter(severity='Low').count(),
            'Medium': Report.objects.filter(severity='Medium').count(),
            'High': Report.objects.filter(severity='High').count(),
            'Critical': Report.objects.filter(severity='Critical').count(),
        }

        # Filter reports based on the selected program and limit to top 5
        program_report_stats = Program.objects.annotate(
            total_reports=Count('report'),
            rewarded_count=Count('report', filter=Q(report__status='Rewarded')),
            duplicate_count=Count('report', filter=Q(report__status='Duplicate')),
            closed_count=Count('report', filter=Q(report__status='Closed')),
            reward_amount=Sum('report__reward', filter=Q(report__status='Rewarded')),
        ).order_by('-reward_amount')[:5]

        status_counts = {
            'New': Report.objects.filter(status='New').count(),
            'Triaged': Report.objects.filter(status='Triaged').count(),
            'Rewarded': Report.objects.filter(status='Rewarded').count(),
            'Closed': Report.objects.filter(status='Closed').count(),
            'Duplicate': Report.objects.filter(status='Duplicate').count(),
        }

        return render(request, 'dashboard/home.html', {
            'total_earned': total_earned,
            'programs': programs,
            'status_counts': status_counts,
            'program_report_stats': program_report_stats,
            'total_report': total_report,
            'severity_counts': severity_counts,
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
        reports = Report.objects.filter(filters).order_by('-updated_at')

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
        
        paginator = Paginator(reports, 10)  # 10 devices per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'reports/reports.html', {
            'reports': page_obj,
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

        messages.success(request, "Report created successfully.")
        return redirect('reports')
    messages.error(request, "Error creating report.")
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

            messages.success(request, "Report updated successfully.")
            return redirect('reports')
        messages.error(request, "Error updating report.")
    return redirect('reports')

@login_required()
def ReportDelete(request, id):
    if request.method == "POST":
        report = get_object_or_404(Report, pk=id)
        
        if report:
            report.delete()
            return JsonResponse({'message': 'Report deleted successfully.', 'status': 'success'}, status=200)
        else:
            return JsonResponse({'message': 'Report not found.', 'status': 'error'}, status=404)
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

        messages.success(request, "Program created successfully.")
        return redirect('programs')
    messages.error(request, "Error creating program.")
    return redirect('programs')

@login_required()
def ProgramEdit(request, id):
    if request.method == "POST":
        program = get_object_or_404(Program, pk=id)
        
        if program:
            program.name = request.POST.get('name')
            program.platform_id = request.POST.get('platform')
            program.save()

            messages.success(request, "Program updated successfully.")
            return redirect('programs')
        messages.error(request, "Error updating program.")
    return redirect('programs')

@login_required()
def ProgramDelete(request, id):
    if request.method == "POST":
        program = get_object_or_404(Program, pk=id)
        
        if program:
            program.delete()
            return JsonResponse({'message': 'Program deleted successfully.', 'status': 'success'}, status=200)
        else:
            return JsonResponse({'message': 'Program not found.', 'status': 'error'}, status=404)
    return redirect('programs')

@login_required()
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

        messages.success(request, "Platform created successfully.")
        return redirect('platforms')
    messages.error(request, "Error creating platform.")
    return redirect('platforms')

@login_required()
def PlatformEdit(request, id):
    if request.method == "POST":
        platform = get_object_or_404(Platform, pk=id)
        
        if platform:
            platform.name = request.POST.get('name')
            platform.save()

            messages.success(request, "Platform updated successfully.")
            return redirect('platforms')
        messages.error(request, "Error updating platform.")
    return redirect('platforms')

@login_required()
def PlatformDelete(request, id):
    if request.method == "POST":
        platform = get_object_or_404(Platform, pk=id)
        if platform:
            platform.delete()
            return JsonResponse({'message': 'Platform deleted successfully.', 'status': 'success'}, status=200)
        else:
            return JsonResponse({'message': 'Platform not found.', 'status': 'error'}, status=404)
    return redirect('platforms')

@login_required()
def ProgramWiseAnalytics(request):
    programs = Program.objects.all()
    
    if request.method == "GET":
        program = request.GET.get('id', '')
        
        if program:
            # Filter reports based on the selected program
            program_report_stats = Program.objects.filter(id=program).annotate(
                total_reports=Count('report'),
                rewarded_count=Count('report', filter=Q(report__status='Rewarded')),
                duplicate_count=Count('report', filter=Q(report__status='Duplicate')),
                closed_count=Count('report', filter=Q(report__status='Closed')),
                reward_amount=Sum('report__reward', filter=Q(report__status='Rewarded')),
            )
        else:
            program_report_stats = Program.objects.annotate(
                total_reports=Count('report'),
                rewarded_count=Count('report', filter=Q(report__status='Rewarded')),
                duplicate_count=Count('report', filter=Q(report__status='Duplicate')),
                closed_count=Count('report', filter=Q(report__status='Closed')),
                reward_amount=Sum('report__reward', filter=Q(report__status='Rewarded')),
            )
        # Paginator for the program report stats
        paginator = Paginator(program_report_stats, 10)  # 10 devices per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    return render(request, 'analytics/program.html', context={"data": page_obj, "programs": programs})

@login_required
def ImportProgram(request):
    if request.method == "POST":
        # Get the uploaded file
        file = request.FILES.get('file')
        
        if file:
            try:
                # Create an instance of ProgramResource
                program_resource = ProgramResource()
                
                # Read and decode the file data into a Dataset
                dataset = Dataset()
                dataset.load(file.read().decode(), format='csv')  # Change format if needed
                
                # Perform a dry run to check for errors before importing
                result = program_resource.import_data(dataset, dry_run=True)
                
                if result.has_errors():
                    # If there are errors, display them
                    for error in result.row_errors():
                        messages.error(request, f"Error in row {error['row']}: {error['error']}")
                else:
                    # Proceed with actual data import
                    program_resource.import_data(dataset, dry_run=False)
                    messages.success(request, "Programs imported successfully.")

            except Exception as e:
                # Handle any exceptions that occur during the import process
                messages.error(request, f"Error importing programs: {str(e)}")
        
        else:
            # If no file was uploaded, inform the user
            messages.error(request, "No file uploaded.")
    else:
        # If the request method is not POST, inform the user
        messages.error(request, "Invalid request method.")
    
    # Redirect to the programs page after the process
    return redirect('programs')

@login_required()
def ImportReport(request):
    if request.method == "POST":
        # Get the uploaded file
        file = request.FILES.get('file')
        
        if file:
            try:
                # Create an instance of ProgramResource
                report_resource = ReportResource()
                
                # Read and decode the file data into a Dataset
                dataset = Dataset()
                dataset.load(file.read().decode(), format='csv')  # Change format if needed
                
                # Perform a dry run to check for errors before importing
                result = report_resource.import_data(dataset, dry_run=True)
                
                if result.has_errors():
                    # If there are errors, display them
                    messages.error(request, f"Errors during import")
                
                else:
                    # Proceed with actual data import
                    report_resource.import_data(dataset, dry_run=False)
                    messages.success(request, "Reports imported successfully.")

            except Exception as e:
                # Handle any exceptions that occur during the import process
                messages.error(request, f"Error importing reports: {str(e)}")
        
        else:
            # If no file was uploaded, inform the user
            messages.error(request, "No file uploaded.")
    else:
        # If the request method is not POST, inform the user
        messages.error(request, "Invalid request method.")
    
    # Redirect to the reports page after the process
    return redirect('reports')