from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.mail import send_mail
from django.conf import settings
from .models import TicketReply
from .models import Ticket , TicketDocument
from .serializers import TicketSerializer
import base64
from django.utils.dateparse import parse_date
from django.core.files.base import ContentFile
from django.http import FileResponse , Http404
from .models import ( Ticket, TicketDocument, TicketStatus, TicketPriority, Category, SubCategory)
from django.core.mail import EmailMessage
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        requester = request.user

        if data.get("user_id"):
            try:
                requested_user = User.objects.get(id=data["user_id"])
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)

            if not requester.is_staff and requested_user.id != requester.id:
                return Response(
                    {"error": "You cannot create a ticket for another user"},
                    status=status.HTTP_403_FORBIDDEN
                )

            ticket_user = requested_user
        else:
            ticket_user = requester

        try:
            if data.get("status_id"):
                data["status"] = TicketStatus.objects.get(id=data["status_id"]).id

            if data.get("priority_id"):
                data["priority"] = TicketPriority.objects.get(id=data["priority_id"]).id

            if data.get("category_id"):
                data["category"] = Category.objects.get(id=data["category_id"]).id

            if data.get("subcategory_id"):
                sub = SubCategory.objects.get(id=data["subcategory_id"])
                if data.get("category_id") and sub.category_id != int(data["category_id"]):
                    return Response(
                        {"error": "SubCategory does not belong to Category"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                data["subcategory"] = sub.id

        except (
            TicketStatus.DoesNotExist,
            TicketPriority.DoesNotExist,
            Category.DoesNotExist,
            SubCategory.DoesNotExist
        ):
            return Response({"error": "Invalid reference ID"}, status=400)

        serializer = TicketSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        ticket = serializer.save(created_by=ticket_user)

        documents = request.data.get("documents", [])
        for doc in documents:
            try:
                filename = doc["filename"]
                content = doc["content"]

                if ";base64," in content:
                    content = content.split(";base64,")[1]

                file_data = base64.b64decode(content)
                file = ContentFile(file_data, name=filename)

                TicketDocument.objects.create(ticket=ticket, file=file)

            except Exception as e:
                return Response(
                    {"error": f"Invalid base64 document format: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        EmailMessage(
            subject=f"Ticket Created: {ticket.title}",
            body=f"""
         Hello {ticket_user.email},

         A support ticket has been created successfully.

         Title: {ticket.title}
         Description: {ticket.description}
         """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ticket_user.email],
        ).send(fail_silently=True)

        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED
        )

    

class TicketReplyCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket not found"}, status=404)

        if not request.user.is_staff:
            if ticket.created_by_id != request.user.id:
                return Response(
                    {"error": "You are not allowed to reply to this ticket"},
                    status=status.HTTP_403_FORBIDDEN
                )

        message = request.data.get("message")
        if not message:
            return Response({"error": "Message is required"}, status=400)

        reply = TicketReply.objects.create(
            ticket=ticket,
            user=request.user,
            message=message
        )

        documents = request.data.get("documents", [])
        saved_documents = []

        for doc in documents:
            try:
                filename = doc["filename"]
                content = doc["content"]

                if ";base64," in content:
                    content = content.split(";base64,")[1]

                file_data = base64.b64decode(content)
                file = ContentFile(file_data, name=filename)

                document = TicketDocument.objects.create(
                    ticket=ticket,
                    reply=reply,
                    file=file
                )

                saved_documents.append({
                    "id": document.id,
                    "file": document.file.url,
                    "uploaded_at": document.uploaded_at
                })

            except Exception as e:
                return Response(
                    {"error": f"Invalid base64 document: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        recipient = (
            ticket.created_by.email
            if request.user.is_staff
            else settings.SUPPORT_EMAIL
        )

        EmailMessage(
            subject=f"Reply on ticket: {ticket.title}",
            body=f"""
            Hello,

            There is a new reply on the ticket.

            Message:
            {message}
            """,

            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        ).send(fail_silently=True)

        return Response(
            {
                "message": "Reply saved successfully",
                "reply": {
                    "id": reply.id,
                    "message": reply.message,
                    "created_at": reply.created_at,
                    "documents": saved_documents
                }
            },
            status=status.HTTP_201_CREATED
        )



class TicketListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self, request):
        user = request.user
        data = request.data if request.method == "POST" else request.query_params

        user_id = data.get("user_id")
        ticket_id = data.get("ticket_id")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if not user.is_staff:
            if user_id or ticket_id:
                return Response(
                    {"error": "You are not authorized to filter tickets"},
                    status=status.HTTP_403_FORBIDDEN
                )
            tickets = Ticket.objects.filter(created_by=user)
        else:
            tickets = Ticket.objects.all()

            if user_id:
                if not User.objects.filter(id=user_id).exists():
                    return Response(
                        {"error": "User not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                tickets = tickets.filter(created_by_id=user_id)

            if ticket_id:
                tickets = tickets.filter(id=ticket_id)
                if not tickets.exists():
                    return Response(
                        {"error": "Ticket not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

        if start_date:
            start = parse_date(start_date)
            if not start:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tickets = tickets.filter(created_at__date__gte=start)

        if end_date:
            end = parse_date(end_date)
            if not end:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tickets = tickets.filter(created_at__date__lte=end)

        return tickets.order_by("-created_at")

    def get(self, request):
        tickets = self.get_queryset(request)

        if isinstance(tickets, Response):
            return tickets

        return Response(
            TicketSerializer(tickets, many=True).data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        tickets = self.get_queryset(request)

        if isinstance(tickets, Response):
            return tickets

        return Response(
            TicketSerializer(tickets, many=True).data,
            status=status.HTTP_200_OK
        )
    


class TicketAssignToView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self , request , ticket_id ):
        if not request.user.is_staff:
            return Response({"message": "only staff can assign tickets"}, status=status.HTTP_403_FORBIDDEN)
        try:
            ticket = Ticket.objects.get(id = ticket_id)
        except Ticket.DoesNotExist:
            return Response({"error" : "Ticket not found!!"} , status=404)
        
        assigned_to_id = request.data.get("assigned_to")

        if not assigned_to_id:
            return Response({"error":"assigned_to_id is required"} , status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assigned_user = User.objects.get(id = assigned_to_id , is_staff = True)
        except User.DoesNotExist:
            return Response({"error":"Assigned user must be staff member"}, status = status.HTTP_400_BAD_REQUEST)
        
        ticket.assigned_to = assigned_user
        ticket.save()

        return Response(
            {
                "message":"Ticket assigned successfully",
                "tickect":{
                    "id": ticket_id,
                    "assigned_to":{
                        "id": assigned_user.id ,
                        "email" : assigned_user.email,
                    }
                }
            }, status = status.HTTP_200_OK
        )




class DownloadDocumentView(APIView):
    permissions_class = [permissions.IsAuthenticated]

    def get(self , request , document_id):

        try:
            document = TicketDocument.objects.select_related("ticket").get(id=document_id)
        except TicketDocument.DoesNOTExist:
            raise Http404("Document not found")
        
        ticket = document.ticket

        if not request.user.is_staff and ticket.created_by != request.user:
            return Response ({"message":"You are not allowed to download this document"}, status=status.HTTP_403_FORBIDDEN)
        

        return FileResponse(document.file.open("rb"),
        as_attachment = True,
        filename=document.file.name.split("/")[-1])