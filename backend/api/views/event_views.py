from django.shortcuts import get_object_or_404
from rest_framework import permissions, response, status
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotFound

from api.permissions import CanEditEventDetails,CanCreateAnEventForGroup
from api.models import Event
from api.serializers import EventSerializer

class EventListView(APIView):
    """
    Can create a new event via this view and get all events that a user is associated with
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), CanCreateAnEventForGroup()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        event = Event.objects.filter(group__members = request.user)
        serialized = EventSerializer(event, many=True)
        return response.Response(data=serialized.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serialized = EventSerializer(data=request.data, context={"request":request})
        if serialized.is_valid():
            serialized.save(creator=request.user)
            return response.Response(data={"message":"Event has been created successfully"}, status=status.HTTP_201_CREATED)
        return response.Response(data={"message":"Event was not created"}, status=status.HTTP_400_BAD_REQUEST)
    
class EventView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanEditEventDetails]

    def get_object(self, pk):
        event = get_object_or_404(Event,pk=pk)
        return event

    def get(self, request, pk):
        event = self.get_object(pk=pk)
        self.check_object_permissions(self.request, event)
        serialized = EventSerializer(event)
        return response.Response(data=serialized.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        try:
            event = self.get_object(pk=pk)
            self.check_object_permissions(self.request, event)
            if event.status != Event.ACTIVE:
                return response.Response(data={"message": "You can only update active events"}, status=status.HTTP_400_BAD_REQUEST)
            
            serialized = EventSerializer(instance=event, data=request.data, context={"request":request})
            if serialized.is_valid():
                serialized.save()
                return response.Response(data=serialized.data, status=status.HTTP_200_OK)
            return response.Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)
        except (PermissionDenied, NotFound) as e:
            raise e
        except Event.DoesNotExist:
            serialized = EventSerializer(data=request.data)
            if serialized.is_valid():
                serialized.save(creator=request.user)
                return response.Response(data=serialized.data, status=status.HTTP_200_OK)
            return  response.Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        data = request.data 
        try:
            event = self.get_object(pk=pk)
            self.check_object_permissions(self.request, event)
            serialized = EventSerializer(data=data, instance=event, partial=True)
            if serialized.is_valid():
                serialized.save()
                return response.Response(data=serialized.data, status=status.HTTP_200_OK)
            return  response.Response(data=serialized.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return response.Response(data={"message":"Event does not exist"}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        try:
            event = self.get_object(pk=pk)
            self.check_object_permissions(self.request, event)
            event.delete()
            return response.Response(data={"message":"Event deleted successfully"}, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return response.Response({"message": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Event.DoesNotExist:
            return response.Response(data={"message":"Event does not exist"}, status=status.HTTP_404_NOT_FOUND)

