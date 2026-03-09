import uuid
from djmoney.models.fields import MoneyField
from django.db import models
from django.contrib.auth.models import User
from djmoney.money import Money
from decimal import Decimal
# Create your models here.


class Menu(models.Model):
    name       = models.CharField(max_length=100)
    url_name   = models.CharField(max_length=100, unique=True)
    icon       = models.CharField(max_length=50, blank=True)
    parent     = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='menu_set')
    order      = models.PositiveIntegerField(default=0)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        db_table = 'tb_menus'

    def __str__(self):
        return self.name


class Permission(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ',   'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    menu     = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='permissions')
    action   = models.CharField(max_length=10, choices=ACTION_CHOICES)
    codename = models.CharField(max_length=150, unique=True)

    class Meta:
        unique_together = ('menu', 'action')
        db_table = 'tb_permissions'

    def save(self, *args, **kwargs):
        if not self.codename:
            self.codename = f"{self.menu.url_name}.{self.action.lower()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.codename


class Role(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')
    is_system   = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_roles'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role       = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    avatar     = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio        = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_user_profiles'

    def __str__(self):
        return f"{self.user.username}'s profile"


class Invitation(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Expired', 'Expired')]

    email      = models.EmailField()
    token      = models.UUIDField(default=uuid.uuid4, unique=True)
    role       = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_invitations'

    def __str__(self):
        return f"Invite for {self.email}"


class Program(models.Model):
    name = models.CharField(max_length=100)
    platform = models.ForeignKey('Platform', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Programs"
        verbose_name = "Program"
        db_table = "tb_programs"

    def __str__(self):
        return self.name


class ProgramFollower(models.Model):
    program   = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='followers')
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_programs')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('program', 'user')
        db_table = 'tb_program_followers'

    def __str__(self):
        return f"{self.user.username} follows {self.program.name}"

    
class Platform(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Platforms"
        verbose_name = "Platform"
        db_table = "tb_platforms"

    def __str__(self):
        return self.name
    
class Report(models.Model):
    SEVERITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )
    STATUS_CHOICES = (
        ('New', 'New'),
        ('Triaged', 'Triaged'),
        ('Rewarded', 'Rewarded'),
        ('Duplicate', 'Duplicate'),
        ('Closed', 'Closed'),
    )

    title         = models.CharField(max_length=100)
    vulnerability = models.CharField(max_length=100)
    program       = models.ForeignKey('Program', on_delete=models.CASCADE)
    severity      = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='New')
    reward        = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)

    # Rich text fields
    description       = models.TextField(blank=True)
    steps_to_reproduce = models.TextField(blank=True)
    impact            = models.TextField(blank=True)
    remediation       = models.TextField(blank=True)

    # Participants
    reporter      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_reports')
    coordinator   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='coordinated_reports')
    developer     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    collaborators = models.ManyToManyField(User, blank=True, related_name='collaborated_reports')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Reports"
        verbose_name = "Report"
        db_table = "tb_reports"
    
    def __str__(self):
        return self.title


class ReportComment(models.Model):
    report     = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(User, on_delete=models.CASCADE)
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        db_table = 'tb_report_comments'

    def __str__(self):
        return f"Comment by {self.author.username} on {self.report.title}"


class UploadedImage(models.Model):
    image       = models.ImageField(upload_to='report_images/%Y/%m/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tb_uploaded_images'

    def __str__(self):
        return f"Image {self.id} by {self.uploaded_by}"


class ProgramLog(models.Model):
    program    = models.ForeignKey('Program', on_delete=models.CASCADE)
    duration   = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Program Logs"
        verbose_name = "Program Log"
        db_table = "tb_program_logs"

    def __str__(self):
        return f"{self.program.name}"