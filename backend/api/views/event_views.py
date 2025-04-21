from rest_framework import permissions, response, status
from rest_framework.views import APIView

from api.permissions import CanEditEventDetails
from api.models import Event
from api.serializers import EventSerializer

class EventListView(APIView):
    """
    Can create a new event via this view and get all events that a user is associated with
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        event = Event.objects.filter(group__members = request.user)
        serialized = EventSerializer(event, many=True)
        return response.Response(data=serialized.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serialized = EventSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save(creator=request.user)
            return response.Response(data={"message":"Event has been created successfully"}, status=status.HTTP_201_CREATED)
        return response.Response(data={"message":"Event was not created"}, status=status.HTTP_400_BAD_REQUEST)
    
class EventView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanEditEventDetails]

    def get_object(self, pk):
        event = Event.objects.get(pk=pk)
        event.check_object_permissions(self.request, event)
        return event

    def get(self, request, pk):
        event = self.get_object(pk=pk)
        serialized = EventSerializer(event)
        return response.Response(data=serialized.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        try:
            event = self.get_object(pk=pk)
            serialized = EventSerializer(instance=event, data=request.data)
            if serialized.is_valid():
                serialized.save()
                return response.Response(data=serialized.data, status=status.HTTP_200_OK)
            return response.Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)
        except event.DoesNotExist:
            serialized = EventSerializer(data=request.data)
            if serialized.is_valid():
                serialized.save(creator=request.user)
                return response.Response(data=serialized.data, status=status.HTTP_200_OK)
            return  response.Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        data = request.data 
        try:
            event = self.get_object(pk=pk)
            serialized = EventSerializer(data=data, instance=event, partial=True)
            if serialized.is_valid():
                serialized.save()
                return response.Response(data=serialized.data, status=status.HTTP_200_OK)
            return  response.Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)
        except event.DoesNotExist:
            return response.Response(data={"message":"Event does not exist"}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        try:
            event = self.get_object(pk=pk)
            event.delete()
            return response.Response(data={"message":"Event deleted successfully"}, status=status.HTTP_200_OK)
        except event.DoesNotExist:
            return response.Response(data={"message":"Event does not exist"}, status=status.HTTP_404_NOT_FOUND)

