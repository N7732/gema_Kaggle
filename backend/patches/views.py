from rest_framework import viewsets
from .models import Patch
from .serializers import PatchSerializer

class PatchViewSet(viewsets.ModelViewSet):
    queryset = Patch.objects.all().order_by('-created_at')
    serializer_class = PatchSerializer
    filterset_fields = ['issue', 'tests_passed', 'agent_mode']
