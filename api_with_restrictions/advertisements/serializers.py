from django.contrib.auth.models import User
from rest_framework import serializers, status

from advertisements.models import Advertisement, FavoriteAdvertisement
# from django.core.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    creator = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'created_at', )

    def create(self, validated_data):
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        if self.context['request'].method in ('PATCH', 'PUT'):
            creator = Advertisement.objects.get(id=self.instance.pk).creator_id
        elif self.context['request'].method == 'POST':
            creator = self.context["request"].user.id
        count = Advertisement.objects.all().filter(creator_id=creator, status='OPEN').count()
        if count > 9:
            if  self.context['request'].method == 'POST' and data['status'] == 'OPEN' or\
                self.context['request'].method in ('PATCH', 'PUT') and\
                    self.instance.status != 'OPEN' and data['status'] == 'OPEN':
                raise serializers.ValidationError('превышено максимальное значение открытых объявлений')
        return data


class FavoriteAdvertisementSerializer(serializers.ModelSerializer):
    favorite_ad = AdvertisementSerializer()

    class Meta:
        model = FavoriteAdvertisement
        fields = ['favorite_ad']

    def create(self, validated_data):
        return super().create(validated_data)

    def validate(self, data):
        if FavoriteAdvertisement.objects.filter(user=data['user'],favorite_ad=data['favorite_ad']):
            raise serializers.ValidationError(
                'Объявление уже находится в избранных.'
            )

        if Advertisement.objects.get(id=data['favorite_ad'].id).creator_id == data['user'].id:
            raise serializers.ValidationError(
                'Данное объявление принадлежит пользователю.'
            )

        if Advertisement.objects.get(id=data['favorite_ad'].id).status == 'DRAFT':
            raise serializers.ValidationError(
                'Объявлния сo статусом DRAFT недоступны.'
            )

        return data

