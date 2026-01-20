from rest_framework import serializers
from .models import ( Ticket,TicketReply,TicketDocument,Category,SubCategory,TicketStatus,TicketPriority)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = "__all__"



class TicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketStatus
        fields = "__all__"


class TicketPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketPriority
        fields = "__all__"



class TicketDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketDocument
        fields = "__all__"


# class TicketReplySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TicketReply
#         fields = "__all__"
#         read_only_fields = ['user', 'created_at']


class TicketReplySerializer(serializers.ModelSerializer):
    documents = TicketDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketReply
        fields = ['id', 'ticket', 'user', 'message', 'created_at', 'documents']
        read_only_fields = ['user', 'created_at']





class TicketSerializer(serializers.ModelSerializer):
    replies = TicketReplySerializer(many=True, read_only=True)
    documents = TicketDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ['created_by', 'created_at', 'updated_at']
