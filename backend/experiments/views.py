from rest_framework import viewsets
from .models import Experiment
from .serializers import ExperimentSerializer

class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all().order_by('-created_at')
    serializer_class = ExperimentSerializer
    filterset_fields = ['variant']
