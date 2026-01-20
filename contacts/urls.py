from django.urls import path
from .import views
from .views import AddContact , GetAllContacts , UpdateContact , DeleteContact , DownloadContacts


urlpatterns = [
    path('global-contacts/add' , AddContact.as_view() , name='addcontacts'),
    path('all-contacts/', GetAllContacts.as_view(), name='all-contacts'),
    path('contacts/update/<int:pk>/' , UpdateContact.as_view()),
    path('contacts/delete/<int:pk>/' , DeleteContact.as_view()),
    path('contacts/download/', DownloadContacts.as_view(), name='download-contacts'),

]
