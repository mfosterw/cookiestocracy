from rest_framework import serializers

from democrasite.webiscite.models import Bill


class BillSerializer(serializers.HyperlinkedModelSerializer):
    author: serializers.RelatedField = serializers.HyperlinkedRelatedField(
        view_name="api:user-detail", lookup_field="username", read_only=True
    )
    yes_votes: serializers.RelatedField = serializers.HyperlinkedRelatedField(
        view_name="api:user-detail", many=True, lookup_field="username", read_only=True
    )
    no_votes: serializers.RelatedField = serializers.HyperlinkedRelatedField(
        view_name="api:user-detail", many=True, lookup_field="username", read_only=True
    )

    class Meta:
        model = Bill
        fields = ["name", "description", "pr_num", "author", "prop_date", "yes_votes", "no_votes", "url"]
        extra_kwargs = {
            "pr_num": {"read_only": True},
            "prop_date": {"read_only": True},
            "url": {"view_name": "api:bill-detail", "lookup_field": "pk"},
        }
