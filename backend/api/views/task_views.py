from rest_framework import views, permissions, response, status, generics, serializers
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.models import Task, TaskCategory, Event, GroupMember, CustomUser
from api.serializers import TaskSerializer, TaskCategorySerializer
from api.permissions import IsAdminOrStaffForDefaultCategory, CanChangeTaskStatus, CanAssignTask, CanCreateTaskForEvent, CanAccessOrModifyTask

class TaskListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, CanCreateTaskForEvent]
    serializer_class = TaskSerializer

    @extend_schema(
        operation_id='list_tasks_by_event',
        parameters=[
            OpenApiParameter(name='event', description='Event ID to filter tasks', required=True, type=int)
        ],
        responses={200: TaskSerializer(many=True)}
    )
    def get(self, request):
        event = request.query_params.get("event")

        if event:
            try:
                event = Event.objects.get(pk=event)
            except Event.DoesNotExist:
                return response.Response({"message": f"Event with ID {event} does not exist"}, status=status.HTTP_404_NOT_FOUND)
            tasks = Task.objects.filter(event=event).select_related('event', 'category', 'assigned_to')
            if not tasks.exists():
                return response.Response({"message":f"There are no tasks for this {event.title}"}, status.HTTP_404_NOT_FOUND)
            serialized = TaskSerializer(instance=tasks, many=True)
            return response.Response(serialized.data, status.HTTP_200_OK)        
        else:
            return response.Response({"message":f"There was no event passed in the query so a list could not be generated"}, status.HTTP_404_NOT_FOUND)

    @extend_schema(request=TaskSerializer, responses={201: TaskSerializer})
    def post(self, request):
        """
        This will allow users to add a Task to an event. 
        """
        user = request.user
        event = request.data.get("event")
        if not event:
            return response.Response({"error": "event is required"},status=status.HTTP_400_BAD_REQUEST)

        event = get_object_or_404(Event, pk=event)
        if event.status != Event.ACTIVE:
            return response.Response({"message":f"The event is no longer active"}, status.HTTP_400_BAD_REQUEST)
            
        if user != event.creator:
            try:
                member_groups = GroupMember.objects.get(group=event.group, user=user)
                if member_groups.role not in [GroupMember.ADMIN, GroupMember.CREATOR]:
                    return response.Response({"error": f"Was unable to create a task for {event.title}"}, status=status.HTTP_403_FORBIDDEN)
            except GroupMember.DoesNotExist:
                return response.Response({"error": "User is not a member of the event's group"}, status=status.HTTP_403_FORBIDDEN)
        serialized = TaskSerializer(data=request.data)
        if serialized.is_valid():
            serialized.save(event=event)
            return response.Response(serialized.data, status.HTTP_201_CREATED)
        return response.Response(serialized.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskView(views.APIView):

    permission_classes = [permissions.IsAuthenticated, CanAccessOrModifyTask]
    serializer_class = TaskSerializer

    def get_object(self,pk):
        task = get_object_or_404(Task.objects.select_related('event', 'category', 'assigned_to'),pk=pk)
        return task

    @extend_schema(operation_id='get_task', responses={200: TaskSerializer})
    def get(self, request, pk):
        """
        This is used to retrieve a single task. So it receives the task id
        """
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        serialized = TaskSerializer(instance=task)
        return response.Response(serialized.data, status=status.HTTP_200_OK)
        
    @extend_schema(request=TaskSerializer, responses={200: TaskSerializer})
    def patch(self, request, pk):
        """
        This is used to edit the task title, assigned, etc
        """
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        serialized = TaskSerializer(instance=task, data=request.data, partial=True, context={"request":request})
        if serialized.is_valid():
            serialized.save()
            return response.Response(serialized.data, status.HTTP_200_OK)
        return response.Response(serialized.errors, status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: None})
    def delete(self, request, pk):
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        user = request.user
        event = task.event
        if event.group:
            try:
                member_groups = GroupMember.objects.get(group=event.group, user=user)
                if user != event.creator and member_groups.role not in [GroupMember.ADMIN, GroupMember.CREATOR]:
                    return response.Response({"message": "Permission denied. User is not an admin or creator in the event's group"}, status.HTTP_403_FORBIDDEN)
            except GroupMember.DoesNotExist:
                return response.Response({"message": "User is not a member of the event's group"}, status.HTTP_403_FORBIDDEN)
        elif user != event.creator:
            return response.Response({"message": "Permission denied. User is not creator of event so can not delete the task"}, status.HTTP_403_FORBIDDEN)
        task.delete()
        return response.Response({"message":"The task has been deleted"},status.HTTP_200_OK)
    
class TaskCategoryListView(generics.ListCreateAPIView):
    queryset = TaskCategory.objects.all().order_by('name')
    serializer_class = TaskCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class TaskCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TaskCategory.objects.all()
    serializer_class = TaskCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrStaffForDefaultCategory]

class TaskAssignmentView(views.APIView):

    permission_classes = [permissions.IsAuthenticated, CanAssignTask]
    serializer_class = TaskSerializer

    def get_object(self, pk):
        return get_object_or_404(
            Task.objects.select_related('event', 'category', 'assigned_to'), pk=pk
        )

    @extend_schema(request=TaskSerializer, responses={200: TaskSerializer})
    def patch(self, request,pk):
        """
        This method allows us to assign the user for a task. It will simply assign a valid user to the object. Only the event creators or group admins can do this.
        """
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        #Ensure that the user is available to be assigned a task
        user_id = request.data.get('assigned_to')
        if not user_id:
            return response.Response({"error": "assigned_to is required"},status=status.HTTP_400_BAD_REQUEST)
        #This checks that the user exists
        assigned_user = get_object_or_404(CustomUser, pk=user_id)

        serialized = TaskSerializer(instance=task, data=request.data, partial=True, context={"request":request})
        if serialized.is_valid():
            serialized.save()
            return response.Response(serialized.data, status.HTTP_200_OK)
        return response.Response(serialized.errors, status.HTTP_400_BAD_REQUEST)
        
class ChangeTaskStatusView(views.APIView):

    permission_classes = [permissions.IsAuthenticated, CanChangeTaskStatus]
    serializer_class = TaskSerializer

    def get_object(self, pk):
        return get_object_or_404(
            Task.objects.select_related('event', 'category', 'assigned_to'), pk=pk
        )

    @extend_schema(request=TaskSerializer, responses={200: TaskSerializer})
    def patch(self, request,pk):
        """
        This method allows us to change the status of the task for a user. The user,in this case, is the assignee or the assigned. 
        """
        task = self.get_object(pk)
        self.check_object_permissions(request, task)
        serialized = TaskSerializer(instance=task, data=request.data, partial=True, context={"request":request})
        if serialized.is_valid():
            serialized.save()
            return response.Response(serialized.data, status.HTTP_200_OK)
        return response.Response(serialized.errors, status.HTTP_400_BAD_REQUEST)