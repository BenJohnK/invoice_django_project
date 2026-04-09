from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal

# Create your models here.

User = get_user_model()


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices', db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', db_index=True)

    due_date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def total_amount(self):
        return self.items.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    
    def paid_amount(self):
        return self.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    def balance_amount(self):
        return self.total_amount() - self.paid_amount()

    def update_status(self):
        new_status = self.status

        if self.paid_amount() >= self.total_amount():
            new_status = 'PAID'
        elif self.due_date < timezone.now().date():
            new_status = 'OVERDUE'
        else:
            new_status = 'PENDING'

        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=['status'])

    def __str__(self):
        return f"Invoice {self.id} - {self.status}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.description} - {self.amount}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CARD', 'Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('UPI', 'UPI'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255, unique=True)

    paid_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().get(id=self.invoice.id)

            if invoice.balance_amount() < self.amount:
                raise ValidationError("Payment exceeds remaining balance")

            super().save(*args, **kwargs)

            invoice.update_status()

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount}"