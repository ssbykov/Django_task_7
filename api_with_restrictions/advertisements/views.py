from django.db.models import Q, QuerySet
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework import status

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, FavoriteAdvertisement
from advertisements.permissions import IsAdminOrIsOwnerOrReadOnly
from advertisements.serializers import AdvertisementSerializer, FavoriteAdvertisementSerializer


class AdvertisementViewSet(ModelViewSet):
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filterset_class = AdvertisementFilter

    def get_queryset(self):
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method."
                % self.__class__.__name__
        )

        queryset = self.filter_queryset(self.queryset)

        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.exclude(Q(status='DRAFT') & ~Q(creator=self.request.user.id))
        elif self.request.user.is_anonymous:
            queryset = queryset.exclude(Q(status='DRAFT'))

        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        return queryset


    def get_permissions(self):
        if self.action in ["favorite", "favorites", "create", "destroy", "update", "partial_update"]:
            return (IsAdminOrIsOwnerOrReadOnly(),)
        return []

    @action(detail=False)
    def favorites(self, request):
        queryset = FavoriteAdvertisement.objects.filter(user=request.user)
        serializer = FavoriteAdvertisementSerializer(queryset, many=True)
        return Response({request.user.username: serializer.data})

    @action(detail=True, methods=['post', 'delete'], serializer_class = FavoriteAdvertisementSerializer)
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            favorite_ad = Advertisement.objects.get(id=pk)
            validated_data ={'favorite_ad': favorite_ad, 'user': request.user}
            serializer = FavoriteAdvertisementSerializer(data=validated_data)
            serializer.validate(data=validated_data)
            serializer.create(validated_data)
            queryset = FavoriteAdvertisement.objects.get(user=request.user, favorite_ad=pk)
            serializer = FavoriteAdvertisementSerializer(queryset, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            favorite_ad = FavoriteAdvertisement.objects.filter(favorite_ad=pk)
            if favorite_ad:
                favorite_ad = FavoriteAdvertisement.objects.get(favorite_ad=pk)
                FavoriteAdvertisement.delete(favorite_ad)
                return Response('Объявление удалено из избранных.', status=status.HTTP_204_NO_CONTENT)
            return Response('Объявления нет в списке избранных.', status=status.HTTP_204_NO_CONTENT)



