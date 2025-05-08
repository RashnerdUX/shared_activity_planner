"""
The purpose of this file is to store email templates for various events. Account creation, event creation, etc.
"""

def clean_body(body_text):
    """Removes leading/trailing whitespace and optional common indentation."""
    import textwrap
    return textwrap.dedent(body_text).strip()

def account_created_email(user_name:str, login_url, site_link, ):
    """
    This is the email sent when a user creates an account
    """
    subject = f"Welcome, {user_name}! Your account is ready."

    body = f"""
        Hi [User Name],

        Welcome to [Your Company/App Name]! We're thrilled to have you join our community.

        Your account has been successfully created. You can now log in and start exploring all that [Your Company/App Name] has to offer.

        Get started:

        Log in here: [Login Page Link]
        Explore our features: [Link to Features Page or Tour, Optional]
        Visit our Help Center: [Link to Help Center, Optional]
        If you have any questions, feel free to reply to this email or visit our support page.

        Welcome aboard!

        Best regards,

        The <Insert Company name> Team
        {site_link}
        akhigbek6@gmail.com
        """
    return subject, clean_body(body)

def account_deleted_email(user_name:str):
    """
    This is the email sent when a user creates an account
    """
    subject = f" Your account has been successfully deleted"

    body = f"""
                Hi {user_name},

                This email confirms that your account with [Your Company/App Name] has been successfully deleted as per your request.

                We're sorry to see you go. If you change your mind in the future, we'd be happy to welcome you back.

                Please note that it may take some time for your information to be fully removed from all our systems.

                If you did not request this account deletion, please contact our support team immediately at [Support Email Address or Link].

                Thank you for your time with [Your Company/App Name].

                Sincerely,

                The [Your Company/App Name] Team
            """
    return subject, clean_body(body)

def password_reset_email(user_name:str, password_reset_link):
    """
    This is the email sent when a user wants to reset their password
    """
    subject = f"Password Reset Request for Your <Insert app name> Account"

    body = f"""
                Hi {user_name},

                We received a request to reset the password for your account with <Insert app name>.

                To reset your password, please click on the link below:

                {password_reset_link}

                This link is only valid for a limited time. If you did not request a password reset, please ignore this email and your password will remain unchanged.

                For security reasons, please do not share this link with anyone.

                If you have any issues, please contact our support team at [Support Email Address or Link].

                Thank you,

                The <Insert team name> Team
            """
    return subject, clean_body(body)


def event_invitation_email(host_name: str, event_name: str, event_description: str, event_datetime: str, event_location: str, event_link: str, rsvp_link_accept: str, rsvp_link_decline: str, rsvp_link_maybe: str, signup_login_link: str = None):
    """
    This email is sent to invite a user to an event.
    """
    subject = f"You're Invited to {event_name}!"

    body = f"""
        Hi,

        You've been invited by {host_name} to the following event:

        Event: {event_name}
        Description: {event_description}
        When: {event_datetime}
        Where: {event_location}

        You can view the full event details here:
        {event_link}

        Please let {host_name} know if you can make it by responding below:

        Accept: {rsvp_link_accept}
        Decline: {rsvp_link_decline}
        Maybe: {rsvp_link_maybe}
"""
    if signup_login_link:
        body += f"""

        If you don't have an account or need to log in to respond:
        {signup_login_link}
"""

    body += f"""

        We hope to see you there!

        Best regards,

        The [Your Company/App Name] Team
        [Your Website Link]
"""
    return subject, clean_body(body)

def invitation_accepted_notification_email(host_name: str, participant_name: str, event_name: str, event_guests_link: str):
    """
    This email notifies the host when a participant accepts an invitation.
    """
    subject = f"{participant_name} Accepted Your Invitation to {event_name}"

    body = f"""
        Hi {host_name},

        Just letting you know that {participant_name} has accepted your invitation to:

        Event: {event_name}

        You can view the updated guest list here:
        {event_guests_link}

        Best regards,

        The [Your Company/App Name] Team
"""
    return subject, clean_body(body)

def invitation_declined_notification_email(host_name: str, participant_name: str, event_name: str, event_guests_link: str):
    """
    This email notifies the host when a participant declines an invitation.
    """
    subject = f"{participant_name} Declined Your Invitation to {event_name}"

    body = f"""
        Hi {host_name},

        Just letting you know that {participant_name} has declined your invitation to:

        Event: {event_name}

        You can view the updated guest list here:
        {event_guests_link}

        Best regards,

        The [Your Company/App Name] Team
"""
    return subject, clean_body(body)


def invitation_maybe_notification_email(host_name: str, participant_name: str, event_name: str, event_guests_link: str):
    """
    This email notifies the host when a participant sets their RSVP to Maybe.
    """
    subject = f"{participant_name} is a Maybe for {event_name}"

    body = f"""
        Hi {host_name},

        Just letting you know that {participant_name} has set their RSVP status to 'Maybe' for:

        Event: {event_name}

        You can view the updated guest list here:
        {event_guests_link}

        Best regards,

        The [Your Company/App Name] Team
"""
    return subject, clean_body(body)


def event_details_updated_email(participant_name: str, host_name: str, event_name: str, event_link: str, update_summary: str = None):
    """
    This email notifies participants when event details are updated.
    """
    subject = f"Update: Details Changed for {event_name}"

    body = f"""
        Hi {participant_name},

        {host_name} has made updates to the following event you're invited to:

        Event: {event_name}
"""
    if update_summary:
        body += f"""
        Summary of changes: {update_summary}
"""

    body += f"""
        Please review the updated details here:
        {event_link}

        Best regards,

        The [Your Company/App Name] Team
"""
    return subject, clean_body(body)


def event_cancelled_email(participant_name: str, host_name: str, event_name: str, event_link: str, cancellation_reason: str = None):
    """
    This email urgently notifies participants that an event has been cancelled.
    """
    subject = f"IMPORTANT: Event Cancelled - {event_name}"

    body = f"""
        Hi {participant_name},

        Please be advised that the following event has been CANCELLED by {host_name}:

        Event: {event_name}
"""
    if cancellation_reason:
        body += f"""
        Reason for cancellation: {cancellation_reason}
"""

    body += f"""
        You can view the event page (which shows the cancellation) here:
        {event_link}

        We apologize for any inconvenience this may cause.

        Best regards,

        The [Your Company/App Name] Team
"""
    return subject, clean_body(body)


def event_reminder_email(participant_name: str, event_name: str, event_datetime: str, event_location: str, event_link: str, days_until_event: int):
    """
    This email sends a reminder about an upcoming event.
    """
    time_until_text = f"in {days_until_event} day{'s' if days_until_event != 1 else ''}" if days_until_event > 0 else "today"

    subject = f"Reminder: {event_name} is {time_until_text}!"

    body = f"""
        Hi {participant_name},

        Just a friendly reminder about the upcoming event:

        Event: {event_name}
        When: {event_datetime}
        Where: {event_location}

        It's happening {time_until_text}!

        View event details:
        {event_link}

        We look forward to seeing you there!

        Best regards,

        The [Your Company/App Name] Team
"""
    return subject, clean_body(body)


def new_comment_notification_email(participant_name: str, commenter_name: str, event_name: str, comment_snippet: str, comment_link: str):
    """
    This email notifies a participant about a new comment on an event they're related to.
    """
    subject = f"New Comment on {event_name}"

    body = f"""
        Hi {participant_name},

        {commenter_name} has posted a new comment on the event:

        Event: {event_name}

        Comment Snippet:
        ---
        {comment_snippet}
        ---

        View the full discussion and reply here:
        {comment_link}

        Best regards,

        The [Your Company/App Name] Team
"""
    return subject, clean_body(body)

def welcome_to_collaboration_email(new_user_name: str, invited_by_name: str, event_name: str, event_link: str, dashboard_link: str, website_link: str):
    """
    This email welcomes a new user who joined specifically through an event invitation.
    """
    subject = f"Welcome to [Your Company/App Name]! You've been invited to {event_name}"

    body = f"""
        Hi {new_user_name},

        Welcome to [Your Company/App Name]!

        You're receiving this email because {invited_by_name} invited you to collaborate on their event:

        Event: {event_name}

        You can view the event details here:
        {event_link}

        [Your Company/App Name] helps you plan and coordinate events with others seamlessly. Explore your dashboard to see all your events:
        {dashboard_link}

        We're excited to have you join!

        Best regards,

        The [Your Company/App Name] Team
        {website_link}
"""
    return subject, clean_body(body)

