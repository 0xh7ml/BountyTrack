from djmoney.models.fields import MoneyField
from django.db import models
from djmoney.money import Money
from decimal import Decimal
# Create your models here.


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

    title = models.CharField(max_length=100)
    vulnerability = models.CharField(max_length=100)
    program = models.ForeignKey('Program', on_delete=models.CASCADE)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='New')
    reward = MoneyField(max_digits=14, decimal_places=2, default_currency='USD', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title
    