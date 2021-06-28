from rest_framework import serializers

from core.models import Tag, Project


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProjectSerializer(serializers.ModelSerializer):
    """Serialize a project"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Project
        fields = (
            'id', 'title', 'description', 'tags', 'price', 'link'
        )
        read_only_fields = ('id',)


class ProjectDetailSerializer(ProjectSerializer):
    """Serialize a project detail"""
    tags = TagSerializer(many=True, read_only=True)
