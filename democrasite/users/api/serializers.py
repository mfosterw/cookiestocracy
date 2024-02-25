from rest_framework import serializers

from democrasite.users.models import User


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["username", "name", "url"]

        extra_kwargs = {
            "url": {"view_name": "user-detail", "lookup_field": "username"},
        }
