from rest_framework import serializers
from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    category = serializers.CharField(
        max_length=100,
        error_messages={
            "blank": "Category cannot be empty.",
            "required": "Category cannot be empty.",
        }
    )

    class Meta:
        model = Expense
        fields = [
            "id",
            "amount",
            "category",
            "note",
            "date",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than 0."
            )
        return value

    def validate_category(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Category cannot be empty."
            )
        return value.strip()