from rest_framework import serializers

from database.models import Collection_Music, Collection, Device


class CollectionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection


class CollectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = [
            'device',
            'id',
            'name'
        ]


class Collection_MusicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection_Music


class CollectionDeleteSerializer(serializers.Serializer):
    collection = serializers.IntegerField(required=True)
    track_id = serializers.IntegerField(required=True)


class CollectionNewSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128, required=True)
    device = serializers.CharField(max_length=36, required=True)
    track_id = serializers.IntegerField(required=True)


class DevcieModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
