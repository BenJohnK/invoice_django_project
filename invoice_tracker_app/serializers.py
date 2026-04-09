from rest_framework import serializers
from .models import Invoice, InvoiceItem, Payment

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'amount']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_method', 'transaction_id', 'paid_at']
        read_only_fields = ['paid_at']

    def validate(self, data):
        invoice = self.context.get('invoice')

        if not invoice:
            raise serializers.ValidationError("Invoice context missing")

        if invoice.balance_amount() < data['amount']:
            raise serializers.ValidationError("Payment exceeds remaining balance")

        return data

    def create(self, validated_data):
        invoice = self.context['invoice']
        return Payment.objects.create(invoice=invoice, **validated_data)


class InvoiceSerializer(serializers.ModelSerializer):
    total_amount = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()
    balance_amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id',
            'title',
            'description',
            'status',
            'due_date',
            'total_amount',
            'paid_amount',
            'balance_amount',
            'created_at',
        ]
        read_only_fields = ['status', 'created_at']

    def get_total_amount(self, obj):
        return obj.total_amount()

    def get_paid_amount(self, obj):
        return obj.paid_amount()

    def get_balance_amount(self, obj):
        return obj.balance_amount()


class InvoiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'title', 'description', 'due_date']

    def create(self, validated_data):
        user = self.context['request'].user
        return Invoice.objects.create(user=user, **validated_data)