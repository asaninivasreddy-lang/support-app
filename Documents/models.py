# from django.db import models
# from django.contrib.auth import get_user_model
# from django.conf import settings 

# User = get_user_model()

# class Document(models.Model):
#     file = models.FileField(upload_to='uploads/')
#     user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="documents")
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.file.name} ({self.user.username})"


from django.db import models
from django.conf import settings

class Document(models.Model):
    file = models.FileField(upload_to='uploads/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="documents")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.file.name} ({self.user.email})"
