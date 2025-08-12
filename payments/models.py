from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()

class Payment(models.Model):
    """Payment transactions model"""
    
    PAYMENT_METHOD_CHOICES = [
        ('sslcommerz', 'SSLCommerz'),
        ('stripe', 'Stripe'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]
    
    transaction_id = models.UUIDField(
        _('Transaction ID'),
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='BDT'
    )
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    gateway_transaction_id = models.CharField(
        _('Gateway Transaction ID'),
        max_length=100,
        blank=True
    )
    gateway_response = models.JSONField(
        _('Gateway Response'),
        default=dict,
        blank=True
    )
    description = models.TextField(
        _('Description'),
        blank=True
    )
    invoice_number = models.CharField(
        _('Invoice Number'),
        max_length=50,
        unique=True,
        blank=True
    )
    paid_at = models.DateTimeField(
        _('Paid At'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.email} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from datetime import datetime
        prefix = 'INV'
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}{timestamp}{self.user.id}"


class Donation(models.Model):
    """Donation model for supporting the platform"""
    
    donor_name = models.CharField(
        _('Donor Name'),
        max_length=200
    )
    donor_email = models.EmailField(
        _('Donor Email'),
        blank=True
    )
    donor_phone = models.CharField(
        _('Donor Phone'),
        max_length=17,
        blank=True
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='BDT'
    )
    message = models.TextField(
        _('Message'),
        blank=True
    )
    is_anonymous = models.BooleanField(
        _('Anonymous Donation'),
        default=False
    )
    payment_method = models.CharField(
        _('Payment Method'),
        max_length=20,
        choices=Payment.PAYMENT_METHOD_CHOICES
    )
    transaction_id = models.CharField(
        _('Transaction ID'),
        max_length=100,
        unique=True
    )
    is_verified = models.BooleanField(
        _('Verified'),
        default=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Donation')
        verbose_name_plural = _('Donations')
        ordering = ['-created_at']
    
    def __str__(self):
        if self.is_anonymous:
            return f"Anonymous - {self.amount} {self.currency}"
        return f"{self.donor_name} - {self.amount} {self.currency}"


class Invoice(models.Model):
    """Invoice model for payments"""
    
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    invoice_pdf = models.FileField(
        _('Invoice PDF'),
        upload_to='invoices/',
        blank=True,
        null=True
    )
    is_sent = models.BooleanField(
        _('Sent to Customer'),
        default=False
    )
    sent_at = models.DateTimeField(
        _('Sent At'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice - {self.payment.invoice_number}"
    
    def generate_pdf(self):
        """Generate PDF invoice using ReportLab"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
        from django.core.files.base import ContentFile
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Add invoice content here
        # This is a simplified example
        
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        
        self.invoice_pdf.save(
            f'invoice_{self.payment.invoice_number}.pdf',
            ContentFile(pdf)
        )
        return self.invoice_pdf