from rest_framework.permissions import BasePermission


class IsPrestador(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.prestador == request.user