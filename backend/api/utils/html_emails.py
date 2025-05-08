from django.conf import settings
from django.utils import timezone


# Define some basic styles and structural HTML
def html_email_wrapper(subject_line, main_content_html, company_name="Your Company/App Name", site_link="#", contact_email="#", support_link="#"):
    """
    Provides a basic HTML wrapper structure for emails.
    """
    # Basic inline styles for compatibility
    styles = """
        font-family: sans-serif;
        line-height: 1.6;
        color: #333333;
    """
    button_styles = """
        display: inline-block;
        padding: 10px 20px;
        margin: 10px 0;
        color: #ffffff;
        background-color: #007bff; /* Primary button color */
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
    """
    link_styles = "color: #007bff; text-decoration: none;"
    footer_styles = "font-size: 0.9em; color: #777777; margin-top: 20px; border-top: 1px solid #eeeeee; padding-top: 15px;"


    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{subject_line}</title>
        <style type="text/css">
            body {{ {styles} margin: 0; padding: 20px; background-color: #f4f4f4; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; }}
            td {{ padding: 20px; }}
            .header {{ background-color: #ffffff; text-align: center; padding-bottom: 10px; }}
            .header h1 {{ margin: 0; color: #333333; font-size: 24px; }}
            .content {{ padding: 20px; }}
            .footer {{ {footer_styles} text-align: center; }}
            a {{ {link_styles} }}
            .button {{ {button_styles} }}
        </style>
    </head>
    <body>
        <table cellpadding="0" cellspacing="0">
            <tr>
                <td class="header">
                    <h1>{company_name}</h1>
                    </td>
            </tr>
            <tr>
                <td class="content">
                    {main_content_html}
                </td>
            </tr>
            <tr>
                <td class="footer">
                    <p>&copy; {company_name} {timezone.now().year}</p> # Requires timezone import
                    <p>
                        <a href="{site_link}" style="{link_styles}">Visit Website</a> |
                        <a href="{contact_email}" style="{link_styles}">Contact Us</a> |
                        <a href="{support_link}" style="{link_styles}">Support</a>
                    </p>
                    </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html

# --- Account Related Templates (HTML) ---
def html_account_created_email(user_name: str, login_url: str, site_link: str, features_url: str = None, help_center_url: str = None, company_name="Your Company/App Name", contact_email="support@[yourcompany.com]"):
    """
    HTML email sent when a user creates an account.
    """
    subject = f"Welcome, {user_name}! Your account is ready."

    # Content for the main part of the email body
    content_html = f"""
    <p>Hi {user_name},</p>

    <p>Welcome to {company_name}! We're thrilled to have you join our community.</p>

    <p>Your account has been successfully created. You can now log in and start exploring all that {company_name} has to offer.</p>

    <p><strong>Get started:</strong></p>
    <p><a href="{login_url}" class="button">Log In Now</a></p>

    <p>Or use this link: <a href="{login_url}">{login_url}</a></p>

    <ul>
        <li>Explore our features: <a href="{features_url}">{features_url}</a></li>
        <li>Visit our Help Center: <a href="{help_center_url}">{help_center_url}</a></li>
    </ul>


    <p>If you have any questions, feel free to reply to this email or contact support at <a href="mailto:{contact_email}">{contact_email}</a>.</p>

    <p>Welcome aboard!</p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """
     # Note: Removed extra site_link/email from plain text example as they are in the wrapper footer

    # Wrap the content in the standard HTML structure
    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email, # Pass contact email to footer
        support_link=contact_email # Use contact email as support link example
    )

    return html_body

def html_account_deleted_email(user_name: str, company_name="Your Company/App Name", support_email="support@[yourcompany.com]", site_link="#"):
    """
    HTML email sent when a user deletes their account.
    """
    subject = f"Your account has been successfully deleted"

    content_html = f"""
    <p>Hi {user_name},</p>

    <p>This email confirms that your account with {company_name} has been successfully deleted as per your request.</p>

    <p>We're sorry to see you go. If you change your mind in the future, we'd be happy to welcome you back.</p>

    <p>Please note that it may take some time for your information to be fully removed from all our systems.</p>

    <p>If you did not request this account deletion, please contact our support team immediately at <a href="mailto:{support_email}">{support_email}</a>.</p>

    <p>Thank you for your time with {company_name}.</p>

    <p>Sincerely,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=support_email,
        support_link=support_email
    )

    return html_body

def html_password_reset_email(user_name: str, password_reset_link: str, company_name="Your Company/App Name", support_email="support@[yourcompany.com]", site_link="#"):
    """
    HTML email sent when a user wants to reset their password.
    """
    subject = f"Password Reset Request for Your {company_name} Account"

    content_html = f"""
    <p>Hi {user_name},</p>

    <p>We received a request to reset the password for your account with {company_name}.</p>

    <p>To reset your password, please click the button below:</p>

    <p><a href="{password_reset_link}" class="button">Reset Your Password</a></p>

    <p>Or use this link: <a href="{password_reset_link}">{password_reset_link}</a></p>


    <p>This link is only valid for a limited time. If you did not request a password reset, please ignore this email and your password will remain unchanged.</p>

    <p>For security reasons, please do not share this link with anyone.</p>

    <p>If you have any issues, please contact our support team at <a href="mailto:{support_email}">{support_email}</a>.</p>

    <p>Thank you,</p>

    <p>The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=support_email,
        support_link=support_email
    )

    return html_body


# --- Event Related Templates (HTML) ---

def html_event_invitation_email(host_name: str, event_name: str, event_description: str, event_datetime: str, event_location: str, event_link: str, rsvp_link_accept: str, rsvp_link_decline: str, rsvp_link_maybe: str, signup_login_link: str = None, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email to invite a user to an event.
    """
    subject = f"You're Invited to {event_name}!"

    content_html = f"""
    <p>Hi,</p>

    <p>You've been invited by {host_name} to the following event:</p>

    <h2>{event_name}</h2>
    <p><strong>Description:</strong> {event_description}</p>
    <p><strong>When:</strong> {event_datetime}</p>
    <p><strong>Where:</strong> {event_location}</p>

    <p>You can view the full event details here:</p>
    <p><a href="{event_link}" class="button">View Event Details</a></p>
    <p>Or use this link: <a href="{event_link}">{event_link}</a></p>

    <p>Please let {host_name} know if you can make it by responding below:</p>

    <p>
        <a href="{rsvp_link_accept}" class="button" style="background-color: #28a745;">Accept</a>
        <a href="{rsvp_link_decline}" class="button" style="background-color: #dc3545;">Decline</a>
        <a href="{rsvp_link_maybe}" class="button" style="background-color: #ffc107;">Maybe</a>
    </p>
"""
    if signup_login_link:
        content_html += f"""
    <p>If you don't have an account or need to log in to respond:</p>
    <p><a href="{signup_login_link}">{signup_login_link}</a></p>
"""

    content_html += f"""
    <p>We hope to see you there!</p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body


def html_invitation_accepted_notification_email(host_name: str, participant_name: str, event_name: str, event_guests_link: str, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email notifies the host when a participant accepts an invitation.
    """
    subject = f"{participant_name} Accepted Your Invitation to {event_name}"

    content_html = f"""
    <p>Hi {host_name},</p>

    <p>Just letting you know that <strong>{participant_name}</strong> has accepted your invitation to:</p>

    <h2>{event_name}</h2>

    <p>You can view the updated guest list here:</p>
    <p><a href="{event_guests_link}" class="button">View Guest List</a></p>
    <p>Or use this link: <a href="{event_guests_link}">{event_guests_link}</a></p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body

def html_invitation_declined_notification_email(host_name: str, participant_name: str, event_name: str, event_guests_link: str, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email notifies the host when a participant declines an invitation.
    """
    subject = f"{participant_name} Declined Your Invitation to {event_name}"

    content_html = f"""
    <p>Hi {host_name},</p>

    <p>Just letting you know that <strong>{participant_name}</strong> has declined your invitation to:</p>

    <h2>{event_name}</h2>

    <p>You can view the updated guest list here:</p>
    <p><a href="{event_guests_link}" class="button">View Guest List</a></p>
     <p>Or use this link: <a href="{event_guests_link}">{event_guests_link}</a></p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body

def html_invitation_maybe_notification_email(host_name: str, participant_name: str, event_name: str, event_guests_link: str, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email notifies the host when a participant sets their RSVP to Maybe.
    """
    subject = f"{participant_name} is a Maybe for {event_name}"

    content_html = f"""
    <p>Hi {host_name},</p>

    <p>Just letting you know that <strong>{participant_name}</strong> has set their RSVP status to 'Maybe' for:</p>

    <h2>{event_name}</h2>

    <p>You can view the updated guest list here:</p>
    <p><a href="{event_guests_link}" class="button">View Guest List</a></p>
    <p>Or use this link: <a href="{event_guests_link}">{event_guests_link}</a></p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body


def html_event_details_updated_email(participant_name: str, host_name: str, event_name: str, event_link: str, update_summary: str = None, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email notifies participants when event details are updated.
    """
    subject = f"Update: Details Changed for {event_name}"

    content_html = f"""
    <p>Hi {participant_name},</p>

    <p>{host_name} has made updates to the following event you're invited to:</p>

    <h2>{event_name}</h2>
"""
    if update_summary:
        content_html += f"""
    <p><strong>Summary of changes:</strong><br>
    {update_summary.replace('\\n', '<br>')}</p> """

    content_html += f"""
    <p>Please review the updated details here:</p>
    <p><a href="{event_link}" class="button">View Updated Event</a></p>
    <p>Or use this link: <a href="{event_link}">{event_link}</a></p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body


def html_event_cancelled_email(participant_name: str, host_name: str, event_name: str, event_link: str, cancellation_reason: str = None, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email urgently notifies participants that an event has been cancelled.
    """
    subject = f"IMPORTANT: Event Cancelled - {event_name}"

    content_html = f"""
    <p>Hi {participant_name},</p>

    <p style="color: #dc3545; font-weight: bold;">Please be advised that the following event has been CANCELLED by {host_name}:</p>

    <h2>{event_name}</h2>
"""
    if cancellation_reason:
        content_html += f"""
    <p><strong>Reason for cancellation:</strong><br>
    {cancellation_reason.replace('\\n', '<br>')}</p> """

    content_html += f"""
    <p>You can view the event page (which shows the cancellation) here:</p>
    <p><a href="{event_link}" class="button">View Event Page</a></p>
    <p>Or use this link: <a href="{event_link}">{event_link}</a></p>


    <p>We apologize for any inconvenience this may cause.</p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body


def html_event_reminder_email(participant_name: str, event_name: str, event_datetime: str, event_location: str, event_link: str, days_until_event: int, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email sends a reminder about an upcoming event.
    """
    time_until_text = f"in {days_until_event} day{'s' if days_until_event != 1 else ''}" if days_until_event > 0 else "today"

    subject = f"Reminder: {event_name} is {time_until_text}!"

    content_html = f"""
    <p>Hi {participant_name},</p>

    <p>Just a friendly reminder about the upcoming event:</p>

    <h2>{event_name}</h2>
    <p><strong>When:</strong> {event_datetime}</p>
    <p><strong>Where:</strong> {event_location}</p>

    <p>It's happening <strong>{time_until_text}</strong>!</p>

    <p>View event details:</p>
    <p><a href="{event_link}" class="button">View Event Details</a></p>
     <p>Or use this link: <a href="{event_link}">{event_link}</a></p>

    <p>We look forward to seeing you there!</p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body


def html_new_comment_notification_email(participant_name: str, commenter_name: str, event_name: str, comment_snippet: str, comment_link: str, company_name="Your Company/App Name", site_link="#", contact_email="#"):
    """
    HTML email notifies a participant about a new comment on an event they're related to.
    """
    subject = f"New Comment on {event_name}"

    content_html = f"""
    <p>Hi {participant_name},</p>

    <p>{commenter_name} has posted a new comment on the event:</p>

    <h2>{event_name}</h2>

    <div style="border-left: 4px solid #007bff; padding-left: 10px; margin: 15px 0; font-style: italic;">
        <p>{comment_snippet.replace('\\n', '<br>')}</p> </div>

    <p>View the full discussion and reply here:</p>
    <p><a href="{comment_link}" class="button">View Comment</a></p>
    <p>Or use this link: <a href="{comment_link}">{comment_link}</a></p>


    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=site_link,
        contact_email=contact_email
    )

    return html_body

def html_welcome_to_collaboration_email(new_user_name: str, invited_by_name: str, event_name: str, event_link: str, dashboard_link: str, website_link: str, company_name="Your Company/App Name", contact_email="#"):
    """
    HTML email welcomes a new user who joined specifically through an event invitation.
    """
    subject = f"Welcome to {company_name}! You've been invited to {event_name}"

    content_html = f"""
    <p>Hi {new_user_name},</p>

    <p>Welcome to {company_name}!</p>

    <p>You're receiving this email because {invited_by_name} invited you to collaborate on their event:</p>

    <h2>{event_name}</h2>
    <p>You can view the event details here:</p>
    <p><a href="{event_link}" class="button">View Event Details</a></p>
    <p>Or use this link: <a href="{event_link}">{event_link}</a></p>


    <p>{company_name} helps you plan and coordinate events with others seamlessly. Explore your dashboard to see all your events:</p>
    <p><a href="{dashboard_link}" class="button">Go to Your Dashboard</a></p>
    <p>Or use this link: <a href="{dashboard_link}">{dashboard_link}</a></p>


    <p>We're excited to have you join!</p>

    <p>Best regards,<br>
    The {company_name} Team</p>
    """

    html_body = html_email_wrapper(
        subject_line=subject,
        main_content_html=content_html,
        company_name=company_name,
        site_link=website_link, # Use website_link for the footer's "Visit Website"
        contact_email=contact_email
    )

    return html_body