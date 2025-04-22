from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from api.models import Event, Participant, GroupMember, CustomUser
from api.serializers import ParticipantSerializer
from django.conf import settings

class ParticipantView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Event, pk=pk)

    def get(self, request, pk):
        event = self.get_object(pk)
        #TODO: Might have to remove this check later to ensure users can be invited
        if not event.group.members.filter(id=request.user.id).exists():
            return Response(
                {"detail": "You must be a group member to view participants"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rsvp_status = request.query_params.get('rsvp_status')
        participants = event.event_participant.all()

        #This shows participants with a certain rsvp status if requested for
        RSVP_CHOICE_MAP = {}
        for value, display in Participant.RSVP_CHOICES:
            RSVP_CHOICE_MAP[value.upper()] = value
            RSVP_CHOICE_MAP[display.upper()] = value
        if rsvp_status:
            if rsvp_status in RSVP_CHOICE_MAP:
                client_rsvp = RSVP_CHOICE_MAP[rsvp_status]
                participants = participants.filter(rsvp_status=client_rsvp)
            else:
                return Response({"message":"Wrong rsvp status passed in query params"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ParticipantSerializer(participants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        event = self.get_object(pk)
        data = {
            "event": event.id,
            "user": request.user.id,
            "rsvp_status": request.data.get("rsvp_status", Participant.PENDING)
        }
        participant = Participant.objects.filter(event=event, user=request.user).first()
        
        #Update or create a participant depending on if the user was linked to the event
        if participant:
            serializer = ParticipantSerializer(participant, data=data, partial=True)
        else:
            serializer = ParticipantSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED if not participant else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        event = self.get_object(pk)
        participant = get_object_or_404(Participant, event=event, user=request.user)
        data = {
            "event": event.id,
            "user": request.user.id,
            "rsvp_status": request.data.get("rsvp_status")
        }
        serializer = ParticipantSerializer(participant, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(pk)
        participant = get_object_or_404(Participant, event=event, user=request.user)
        participant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class InvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Event, pk=pk)

    def post(self, request, pk):
        """
        Invite group members to an event. Only group admins/creators can invite.
        """
        event = self.get_object(pk)
        #This ensures only Group admins and creators can send an invite
        #TODO: Transfer to a permissions class if possible after fixing the few
        if not GroupMember.objects.filter(
            group=event.group,
            user=request.user,
            role__in=[GroupMember.ADMIN, GroupMember.CREATOR]
        ).exists():
            return Response(
                {"detail": "Only group admins or creators can send invitations"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_ids = request.data.get('user_ids', [])
        #Check if no user_ids were passed in the payload
        if not user_ids:
            return Response(
                {"detail": "user_ids list is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #This list stores the participants who were successfully invited
        created = []
        #This list stores the participants who weren't invited 
        errors = []

        #Send the invites by linking participants to the event
        for user_id in user_ids:
            try:
                #If user doesn't exist, then return a 404
                try:
                    user = CustomUser.objects.get(pk=user_id)
                except CustomUser.DoesNotExist:
                    errors.append(f"User {user_id}: The User was not found in the database")
                    continue

                #If user is already a participant, skip invite
                if Participant.objects.filter(event=event, user=user).exists():
                    errors.append(f"User {user_id} is already a participant")
                    continue
                
                participant = Participant.objects.create(
                    event=event,
                    user=user,
                    rsvp_status=Participant.PENDING
                )
                created.append(ParticipantSerializer(participant).data)
            except ValidationError as e:
                errors.append(f"User {user_id}: {str(e)}")
        
        response_data = {"created": created}
        if errors:
            response_data["errors"] = errors
            status_code = status.HTTP_207_MULTI_STATUS if created else status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_201_CREATED
        
        return Response(response_data, status=status_code)