from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum

# Call the models
from .models import Program, Platform, Report

# Create your views here.
def home(request):
    if request.method == "GET":
        new_reports = Report.objects.filter(status='New').count()
        rewarded_reports = Report.objects.filter(status='Rewarded').count()
        rejected_reports = Report.objects.filter(status__in=['Closed', 'Duplicate']).count()
        triaged_reports = Report.objects.filter(status='Triaged').count()
        total_earned = Report.objects.filter(status='Rewarded').aggregate(Sum('reward'))['reward__sum'] or 0

        return render(request, 'home.html', {
            'new_reports': new_reports,
            'rewarded_reports': rewarded_reports,
            'rejected_reports': rejected_reports,
            'triaged_reports': triaged_reports,
            'total_earned': total_earned
        })


def reports(request):
    if request.method == "GET":
        reports = Report.objects.all().order_by('-created_at')
        platforms = Platform.objects.all()
        programs = Program.objects.all()
        paginator = Paginator(reports, 10)  # 10 devices per page
        
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'reports.html', {
            'reports': page_obj, 
            'severities': Report.SEVERITY_CHOICES, 
            'statuses': Report.STATUS_CHOICES,
            'platforms': platforms,
            'programs': programs
        })
 
def platform(request):
    return render(request, 'platform.html')

def program_name(request):
    return render(request, 'program_name.html')
