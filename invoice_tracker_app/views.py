from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Invoice
from .serializers import (
    InvoiceCreateSerializer,
    InvoiceItemSerializer,
    InvoiceSerializer,
    PaymentSerializer,
)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return InvoiceCreateSerializer
        return InvoiceSerializer

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        invoice = self.get_object()

        serializer = InvoiceItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(invoice=invoice)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def add_payment(self, request, pk=None):
        invoice = self.get_object()

        serializer = PaymentSerializer(
            data=request.data,
            context={"invoice": invoice},
        )

        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        invoice = self.get_object()

        data = {
            "invoice_id": invoice.id,
            "total_amount": invoice.total_amount(),
            "paid_amount": invoice.paid_amount(),
            "balance_amount": invoice.balance_amount(),
            "status": invoice.status,
        }

        return Response(data)