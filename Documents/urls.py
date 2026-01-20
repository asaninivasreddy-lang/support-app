from django.urls import path
from .views import UploadDocumentView,ListUserDocumentsView,UpdateDocumentView,DeleteDocumentView,DownloadDocumentView

urlpatterns = [
    path('documents/upload/', UploadDocumentView.as_view(), name='upload-document'),
    path('documents/user/<int:user_id>/', ListUserDocumentsView.as_view(), name='list-user-documents'),
    path('documents/<int:user_id>/<int:doc_id>/update/', UpdateDocumentView.as_view(), name='update-document'),
    path('documents/<int:user_id>/<int:doc_id>/delete/', DeleteDocumentView.as_view(), name='delete-document'),
    path('documents/download/<int:user_id>/<int:doc_id>/', DownloadDocumentView.as_view(), name='download-document'),
]
