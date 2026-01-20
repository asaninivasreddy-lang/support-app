from django.urls import path
from .views import ( TicketCreateView,TicketReplyCreateView,TicketListView,TicketAssignToView , DownloadDocumentView)

urlpatterns = [
    path("tickets/create/", TicketCreateView.as_view()),
    path("tickets/reply/<int:ticket_id>/", TicketReplyCreateView.as_view()),
    path("tickets/", TicketListView.as_view(), name="ticket-list"),
    path("tickets/<int:ticket_id>/assign", TicketAssignToView.as_view(), name="ticket-assign"),
    path("documents/<int:document_id>/download/", DownloadDocumentView.as_view() , name = "document-download"),
]
