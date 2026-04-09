from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Invoice
from .serializers import (InvoiceCreateSerializer, InvoiceItemSerializer,
                          InvoiceSerializer, PaymentSerializer)

# Create your views here.



class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = Invoice.objects.all()

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return InvoiceCreateSerializer
        return InvoiceSerializer

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        invoice = self.get_object()

        serializer = InvoiceItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(invoice=invoice)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_payment(self, request, pk=None):
        invoice = self.get_object()

        serializer = PaymentSerializer(data=request.data, context={"invoice": invoice})

        if serializer.is_valid():
            payment = serializer.save()
            return Response(
                PaymentSerializer(payment).data, status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
