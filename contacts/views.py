import csv
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GlobalContacts
from .serializers import GlobalContactsSerializer
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
import re
from django.core.exceptions import ValidationError
from io import StringIO , BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.permissions import AllowAny
import os


def validate_phone_number(phone):
    if not phone:
        raise ValidationError("Phone number is required")

    phone = phone.replace(" ", "")

    pattern = r'^\+?[1-9]\d{6,14}$'
    if not re.fullmatch(pattern, phone):
        raise ValidationError("Invalid phone number format")

    return phone



class AddContact(APIView):
    """
    Add contacts via Base64-encoded CSV or single contact via JSON.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        csv_base64 = request.data.get("file_base64")
        if csv_base64:
            try:
                decoded_file = base64.b64decode(csv_base64)
                file_data = StringIO(decoded_file.decode("utf-8"))
            except Exception:
                return Response({"error": "Invalid Base64 file."}, status=400)

            reader = csv.DictReader(file_data)
            contacts_to_create = []

            existing_names = {n.strip().lower() for n in GlobalContacts.objects.values_list('name', flat=True)}
            existing_phones = {p.strip() for p in GlobalContacts.objects.values_list('phone_number', flat=True)}

            for row in reader:
                name = row.get('name') or row.get('first name') or row.get('firstname')
                phone = row.get('phone_number') or row.get('mobile number') or row.get('phone')

                if not name or not phone:
                    continue

                name = name.strip().lower()
                phone = phone.strip()

                error = validate_phone_number(phone)
                if error:
                    continue

                if name in existing_names or phone in existing_phones:
                    continue

                contacts_to_create.append(GlobalContacts(name=name, phone_number=phone))
                existing_names.add(name)
                existing_phones.add(phone)

            if not contacts_to_create:
                return Response({"message": "No contacts were added. Check CSV data."}, status=400)

            with transaction.atomic():
                GlobalContacts.objects.bulk_create(contacts_to_create)

            return Response({"message": f"{len(contacts_to_create)} contacts added successfully"}, status=201)

        serializer = GlobalContactsSerializer(data=request.data)

        phone = request.data.get('phone_number')
        if phone:
            error = validate_phone_number(phone)
            if error:
                return Response({"phone_number": error}, status=400)

        if serializer.is_valid():
            name = serializer.validated_data['name'].strip().lower()
            phone = serializer.validated_data['phone_number'].strip()

            if GlobalContacts.objects.filter(name__iexact=name).exists():
                return Response({"error": "Name already exists"}, status=400)

            if GlobalContacts.objects.filter(phone_number=phone).exists():
                return Response({"error": "Phone number already exists"}, status=400)

            serializer.save()
            return Response({"message": "Contact added successfully"}, status=201)

        return Response(serializer.errors, status=400)


class GetAllContacts(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        contacts = GlobalContacts.objects.all()

    
        search_query = request.GET.get('search', None)
        if search_query:
            contacts = contacts.filter(name__icontains=search_query) | contacts.filter(phone_number__icontains=search_query)

      
        if 'page' in request.GET:
            paginator = PageNumberPagination()
            paginator.page_size = request.GET.get('page_size', 5 )
            result_page = paginator.paginate_queryset(contacts, request)
            serializer = GlobalContactsSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
       
        serializer = GlobalContactsSerializer(contacts, many=True)
        return Response(serializer.data)


class DownloadContacts(APIView):
    """
    Download contacts only in Base64 format (CSV or PDF) and save to MEDIA_ROOT.
    Query params:
      - search: filter by name or phone
      - file_type: 'base64_csv' or 'base64_pdf'
    """

    permission_classes = [AllowAny]

    def get(self, request):
        search_query = request.GET.get('search', None)
        file_type = request.GET.get('file_type', 'base64_csv').lower()

        contacts = GlobalContacts.objects.all()
        if search_query:
            contacts = contacts.filter(name__icontains=search_query) | contacts.filter(phone_number__icontains=search_query)

        def generate_csv():
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Name', 'Phone Number'])
            for c in contacts:
                writer.writerow([c.name, c.phone_number])
            return output.getvalue()

        def generate_pdf():
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y = height - 50
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, "Contacts")
            y -= 30
            p.setFont("Helvetica", 12)
            for c in contacts:
                if y < 50:
                    p.showPage()
                    y = height - 50
                p.drawString(50, y, f"{c.name} - {c.phone_number}")
                y -= 20
            p.showPage()
            p.save()
            buffer.seek(0)
            return buffer

        if file_type == 'base64_csv':
            csv_data = generate_csv()
            csv_bytes = csv_data.encode('utf-8')
            base64_csv = base64.b64encode(csv_bytes).decode('utf-8')

            file_name = 'contacts/contacts.csv'
            path = default_storage.save(file_name, ContentFile(csv_bytes))
            file_url = os.path.join(settings.MEDIA_URL, path)

            return Response({
                "file_base64": base64_csv,
                "file_url": file_url
            }, status=200)

        elif file_type == 'base64_pdf':
            pdf_buffer = generate_pdf()
            pdf_bytes = pdf_buffer.read()
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

            file_name = 'contacts/contacts.pdf'
            path = default_storage.save(file_name, ContentFile(pdf_bytes))
            file_url = os.path.join(settings.MEDIA_URL, path)

            return Response({
                "file_base64": base64_pdf,
                "file_url": file_url
            }, status=200)

        return Response(
            {"error": "Invalid file_type. Use 'base64_csv' or 'base64_pdf'."},
            status=400
        )

class UpdateContact(APIView):
    permission_classes = [AllowAny]
    def patch(self, request, pk):
        if not request.data:
            return Response({"error": "No data provided to update"}, status=400)

        contact = get_object_or_404(GlobalContacts, pk=pk)

        no_change = True
        for field, value in request.data.items():
            if hasattr(contact, field) and getattr(contact, field) != value:
                no_change = False
                break

        if no_change:
            return Response({"error": "Provided data is same as existing data"}, status=400)

        phone = request.data.get('phone_number')
        if phone:
            error = validate_phone_number(phone)
            if error:
                return Response({"phone_number": error}, status=400)

        name = request.data.get('name')
        if name and GlobalContacts.objects.exclude(pk=pk).filter(name=name).exists():
            return Response({"error": "Name already exists"}, status=400)

        if phone and GlobalContacts.objects.exclude(pk=pk).filter(phone_number=phone).exists():
            return Response({"error": "Phone number already exists"}, status=400)

        serializer = GlobalContactsSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Contact updated successfully", "data": serializer.data}, status=200)

        return Response(serializer.errors, status=400)


class DeleteContact(APIView):
    permission_classes = [AllowAny]
    def delete(self, request, pk):
        contact = get_object_or_404(GlobalContacts, pk=pk)
        contact.delete()
        return Response({"message": "Contact deleted successfully"}, status=200)









































# def validate_phone_number(phone):
#     if not phone:
#         return "Phone number is required"
#     phone = phone.replace(" ", "")
#     pattern = r'^(\+\d{1,3}\d{7,15}|\d{7,15})$'
#     if not re.fullmatch(pattern, phone):
#         return "Invalid phone number format"
#     return None