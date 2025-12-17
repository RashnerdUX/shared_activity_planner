from rest_framework.views import APIView
from rest_framework import response, status, permissions
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import Count, Max
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.models import TimeOption, TimeVote, Event, GroupMember, Participant
from api.serializers import TimeOptionSerializer, TimeVoteSerializer
from api.permissions import CanCreateATimeOption, CanVoteOnEventAndModifyVote

class TimeOptionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TimeOptionSerializer

    @extend_schema(
        operation_id='list_time_options_by_event',
        parameters=[
            OpenApiParameter(name='event', description='Event ID to filter time options', required=True, type=int)
        ],
        responses={200: TimeOptionSerializer(many=True)}
    )
    def get(self, request):
        """
        This retrieves all the time options for a view
        """
        event = request.query_params.get("event")
        try:
            event_timeoptions = TimeOption.objects.filter(event=event)
            serialized = TimeOptionSerializer(event_timeoptions, many=True)
            return response.Response(serialized.data, status.HTTP_200_OK)
        except TimeOption.DoesNotExist:
                return response.Response({"message":"Could not find time option"}, status.HTTP_404_NOT_FOUND)


class TimeOptionView(APIView):
    serializer_class = TimeOptionSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), CanCreateATimeOption()]
        return [permissions.IsAuthenticated()]

    def get_object(self,pk):
        time = get_object_or_404(TimeOption,pk=pk)
        return time

    @extend_schema(operation_id='get_time_option', responses={200: TimeOptionSerializer})
    def get(self, request, pk):
        """
        A single Time option can be retrieved 
        """
        try:
            time = self.get_object(pk)
            serialized = TimeOptionSerializer(instance=time)
            return response.Response(serialized.data, status.HTTP_200_OK)
        except TimeOption.DoesNotExist:
                return response.Response({"message":"Could not find time option"}, status.HTTP_404_NOT_FOUND)
    
    @extend_schema(request=TimeOptionSerializer, responses={201: TimeOptionSerializer})
    def post(self, request, pk):
        """
        This will allow users to add a Timeoption to an event. It will only be accessible to the creator of an event and/or the admins of the group it is associated with. So pk expected here is the event's id
        """
        user = request.user
        try:
            event = Event.objects.get(pk=pk)
            if event.status != Event.ACTIVE:
                return response.Response({"message":f"The event is no longer active"}, status.HTTP_400_BAD_REQUEST)
            
            member_groups = GroupMember.objects.get(group=event.group, user=user)
            if user == event.creator or member_groups.role in [GroupMember.ADMIN, GroupMember.CREATOR]:
                serialized = TimeOptionSerializer(data=request.data)
                if serialized.is_valid():
                    serialized.save(event=event)
                    return response.Response(serialized.data, status.HTTP_201_CREATED)
                else:
                    return response.Response(serialized.errors, status.HTTP_400_BAD_REQUEST)
            else:
                return response.Response({"message":f"Was unable to create a time option for {event.title}"}, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return response.Response({"message":f"The event does not exist", "error":f"{e}"}, status.HTTP_400_BAD_REQUEST)
            
    @extend_schema(request=TimeOptionSerializer, responses={200: TimeOptionSerializer})
    def patch(self, request, pk):
        """
        No need for a put request. A previous time option's datetime is the only thing that can be edited and whether or not it is the final choice
        This can be used to set the start_time or end_time
        """
        try:
            time = self.get_object(pk)
            serialized = TimeOptionSerializer(instance=time, data=request.data, partial=True)
            if serialized.is_valid():
                serialized.save()
                return response.Response(serialized.data, status.HTTP_200_OK)
        except TimeOption.DoesNotExist:
            return response.Response({"message":"Unable to update the time option"}, status.HTTP_400_BAD_REQUEST)

    @extend_schema(responses={200: None})
    def delete(self, request, pk):
        time = self.get_object(pk)
        user = request.user
        event = time.event
        if event.group:
            try:
                member_groups = GroupMember.objects.get(group=event.group, user=user)
                if user != event.creator and member_groups.role not in [GroupMember.ADMIN, GroupMember.CREATOR]:
                    return response.Response({"message": "Permission denied"}, status.HTTP_403_FORBIDDEN)
            except GroupMember.DoesNotExist:
                return response.Response({"message": "User is not a member of the event's group"}, status.HTTP_403_FORBIDDEN)
        elif user != event.creator:
            return response.Response({"message": "Permission denied"}, status.HTTP_403_FORBIDDEN)
        time.delete()
        return response.Response({"message": "Successfully deleted the time option"}, status.HTTP_200_OK)

class TimeVotingView(APIView):
    """
    This is where voting will take place. The client will pass in their time option and then the system will register that as a vote. Voting can be carried out by anyone attending an event irrespective of their role
    """
    permission_classes = [permissions.IsAuthenticated, CanVoteOnEventAndModifyVote]
    serializer_class = TimeVoteSerializer

    @extend_schema(operation_id='cast_time_vote', request=TimeVoteSerializer, responses={200: None})
    def post(self, request, pk):
        event = Event.objects.get(pk=pk)
        data = request.data
        serialized = TimeVoteSerializer(data=data, context={"event":event, "request":request})
        if serialized.is_valid():
            serialized.save(user=request.user)
            time_date = TimeOption.objects.get(pk=data["time_option"]).start_time
            return response.Response({"message":f"Your vote has been casted for {event.title} to hold on {time_date}"}, status.HTTP_200_OK)
        return response.Response({"message":f"Your vote could not be casted for the event"}, status.HTTP_400_BAD_REQUEST)
        
    
    @extend_schema(operation_id='update_time_vote', request=TimeVoteSerializer, responses={200: None})
    def patch(self, request, pk):
        """
        This is updating the voting for a specific user for a certain event so I am receiving the vote id
        """
        try:    
            vote = TimeVote.objects.get(pk=pk)
            event = vote.time_option.event
            data = request.data
            serialized = TimeVoteSerializer(instance=vote, data=data, context={"request": request, "event": event}, partial=True)
            if serialized.is_valid():
                serialized.save()
                return response.Response({"message":f"Your vote has been updated successfully"}, status.HTTP_200_OK)
            return response.Response({"message":f"Your vote could not be updated", "errors": serialized.errors}, status.HTTP_400_BAD_REQUEST)
        except TimeVote.DoesNotExist:
            return response.Response({"message": "Vote does not exist"},status=status.HTTP_404_NOT_FOUND)
    
class GetTimeVotesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TimeOptionSerializer

    @extend_schema(responses={200: TimeOptionSerializer(many=True)})
    def get(self, request, pk):
        """
        This view's sole function is to return an annotated data of all time options associated with an event and their vote count. So, id passed is for the event
        """
        event = Event.objects.get(pk=pk)
        if not event:
            return response.Response({"message": "Event does not exist"},status=status.HTTP_404_NOT_FOUND)

        time_options = TimeOption.objects.filter(event=event).annotate(no_of_votes=Count("votes"))

        if time_options:
            serialized = TimeOptionSerializer(instance=time_options, many=True)
            return response.Response(serialized.data, status.HTTP_200_OK)
        
        return response.Response(serialized.errors, status.HTTP_400_BAD_REQUEST)
    
class ScheduleEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TimeOptionSerializer

    @extend_schema(responses={200: None})
    def post(self, request, pk):
        """
        This is for setting the final time for the event and it will be called when the time for voting ends or if a group doesn't bother voting for the final time of an event. Thus, the event id is required
        """
        event = Event.objects.get(pk=pk)
        time_options= TimeOption.objects.filter(event=event)
        if not time_options:
            return response.Response({"message":"There are no time options associated with the event"}, status.HTTP_404_NOT_FOUND)
        
        #Add the number of votes to each time_option
        timeoption_with_votes = time_options.annotate(vote_count=Count("votes"))
        #Get the maximum votes
        max_vote = timeoption_with_votes.aggregate(max_vote=Max("vote_count"))["max_vote"]
        #Get the time option with most votes
        top_voted_time_option = timeoption_with_votes.filter(vote_count=max_vote)
        #Get the datetime for the event
        chosen_time = top_voted_time_option.first().start_time

        schedule_success = event.set_final_date(date_time=chosen_time)
        if schedule_success:
            return response.Response({"message":f"The final date for the {event.title} is set as {chosen_time}"}, status.HTTP_200_OK)
        else:
            return response.Response({"message":"The final date for the event could not be set"}, status.HTTP_400_BAD_REQUEST)