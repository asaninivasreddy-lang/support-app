from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status 
import  base64
from .utils import base64_to_file
from .models import Document
from .serializers import DocumentSerializer
from django.http import FileResponse, Http404
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
User = get_user_model()


class UploadDocumentView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def post(self, request):
        user_id = request.data.get('user_id')
        file_base64 = request.data.get('file_base64')
        file_name = request.data.get('file_name')

        if not user_id or not file_base64 or not file_name:
            return Response(
                {"error": "user_id, file_name and file_base64 are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        file = base64_to_file(file_base64, file_name)
        if not file:
            return Response({"error": "Invalid base64 file"}, status=status.HTTP_400_BAD_REQUEST)

        document = Document.objects.create(user=user, file=file)
        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ListUserDocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user != user and not request.user.is_staff and not request.user.is_superuser:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        documents = Document.objects.filter(user=user)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)


class UpdateDocumentView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def put(self, request, user_id ,  doc_id ):
        file_base64 = request.data.get('file_base64')
        file_name = request.data.get('file_name')

        if not file_base64 or not file_name:
            return Response(
                {"error": "file_name and file_base64 are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            document = Document.objects.get(id=doc_id, user=user)
        except (User.DoesNotExist, Document.DoesNotExist):
            return Response({"error": "User or document not found"}, status=status.HTTP_404_NOT_FOUND)

        if document.file:
            document.file.delete(save=False)

        file = base64_to_file(file_base64, file_name)
        if not file:
            return Response({"error": "Invalid base64 file"}, status=status.HTTP_400_BAD_REQUEST)

        document.file = file
        document.save()

        serializer = DocumentSerializer(document)
        return Response(serializer.data)



class DeleteDocumentView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def delete(self, request,user_id,doc_id ):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            document = Document.objects.get(id=doc_id, user=user)
        except Document.DoesNotExist:
            return Response({"error": "Document not found for this user"}, status=status.HTTP_404_NOT_FOUND)

        if document.file:
            document.file.delete(save=False)
        document.delete()
        return Response({"message": "Document deleted"},  status=status.HTTP_200_OK)



class DownloadDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, doc_id):
        try:
            user = User.objects.get(id=user_id)
            document = Document.objects.get(id=doc_id, user=user)
        except (User.DoesNotExist, Document.DoesNotExist):
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user != user and not request.user.is_staff and not request.user.is_superuser:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        with document.file.open('rb') as f:
            encoded_file = base64.b64encode(f.read()).decode('utf-8')

        return Response({
            "file_name": document.file.name,
            "file_base64": encoded_file
        })
