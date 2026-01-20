
from django.db import models
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver




class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('category', 'name') 
    def __str__(self):
        return f"{self.category.name} -> {self.name}"



class TicketStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)  

    class Meta:
        verbose_name_plural = "Ticket Statuses"

    def __str__(self):
        return self.name



class TicketPriority(models.Model):
    name = models.CharField(max_length=50, unique=True) 
    level = models.PositiveIntegerField() 

    class Meta:
        ordering = ['level']

    def __str__(self):
        return self.name


class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,related_name='assigned_tickets' )
    status = models.ForeignKey(TicketStatus, on_delete=models.SET_NULL, null=True)
    priority = models.ForeignKey(TicketPriority, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"



class TicketReply(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.user.email} on {self.ticket.title}"


class TicketDocument(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    reply = models.ForeignKey(
        TicketReply,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True
    )
    file = models.FileField(upload_to='ticket_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Document for {self.ticket.title}"

