from rest_framework import permissions
from rest_framework.generics import RetrieveUpdateAPIView
from ..serializers import ProfileSerializer



class ProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile