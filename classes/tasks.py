from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from .models import Assessment, ClassSession
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_assessment_notification(assessment_id):
    """
    Send notification when new assessment is submitted
    """
    try:
        assessment = Assessment.objects.get(id=assessment_id)
        
        # Send email to admin
        subject = f'New Assessment Submission - {assessment.full_name}'
        message = f"""
        New assessment received:
        
        Name: {assessment.full_name}
        Phone: {assessment.phone_number}
        Email: {assessment.email or 'Not provided'}
        Preferred Course: {assessment.preferred_course.title if assessment.preferred_course else 'Not specified'}
        Trial Date: {assessment.trial_date or 'Not specified'}
        Trial Time: {assessment.trial_time or 'Not specified'}
        Notes: {assessment.notes or 'None'}
        
        Please review and assign a teacher.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['admin@amarquran.com'],
            fail_silently=False,
        )
        
        # Send WhatsApp notification using Twilio
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            whatsapp_message = f"""
*New Assessment Submission*

Name: {assessment.full_name}
Phone: {assessment.phone_number}
Course: {assessment.preferred_course.title if assessment.preferred_course else 'Not specified'}

Please check admin panel for details.
            """
            
            message = client.messages.create(
                body=whatsapp_message,
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=settings.ADMIN_WHATSAPP_NUMBER
            )
            
            logger.info(f"WhatsApp notification sent: {message.sid}")
        
        # Mark notification as sent
        assessment.notification_sent = True
        assessment.save()
        
        return True
        
    except Assessment.DoesNotExist:
        logger.error(f"Assessment {assessment_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending assessment notification: {str(e)}")
        return False


@shared_task
def send_class_reminder(session_id):
    """
    Send reminder for upcoming class session
    """
    try:
        session = ClassSession.objects.get(id=session_id)
        
        # Prepare reminder message
        reminder_text = f"""
Reminder: You have a class scheduled

Course: {session.course.title}
Date: {session.date}
Time: {session.start_time} - {session.end_time}
Platform: {session.get_platform_display()}
Meeting Link: {session.meeting_link or 'Will be shared soon'}

Teacher: {session.teacher.get_full_name()}
Student: {session.student.get_full_name()}
        """
        
        # Send email reminders
        recipients = [session.student.email, session.teacher.email]
        send_mail(
            f'Class Reminder - {session.course.title}',
            reminder_text,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        
        # Send WhatsApp reminders if configured
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Send to student if phone number exists
            if session.student.phone_number:
                try:
                    client.messages.create(
                        body=reminder_text,
                        from_=settings.TWILIO_WHATSAPP_NUMBER,
                        to=f"whatsapp:{session.student.phone_number}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp to student: {e}")
            
            # Send to teacher if phone number exists
            if session.teacher.phone_number:
                try:
                    client.messages.create(
                        body=reminder_text,
                        from_=settings.TWILIO_WHATSAPP_NUMBER,
                        to=f"whatsapp:{session.teacher.phone_number}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send WhatsApp to teacher: {e}")
        
        session.reminder_sent = True
        session.save()
        
        return True
        
    except ClassSession.DoesNotExist:
        logger.error(f"Session {session_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending class reminder: {str(e)}")
        return False


@shared_task
def generate_weekly_report():
    """
    Generate weekly reports for admin
    """
    from datetime import datetime, timedelta
    from payments.models import Payment
    from django.db.models import Sum, Count
    import csv
    import io
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    # Get data
    payments = Payment.objects.filter(
        created_at__date__range=[start_date, end_date]
    )
    
    sessions = ClassSession.objects.filter(
        date__range=[start_date, end_date]
    )
    
    # Create CSV report
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Payment summary
    writer.writerow(['Weekly Payment Report'])
    writer.writerow(['Date Range', f'{start_date} to {end_date}'])
    writer.writerow([])
    writer.writerow(['Transaction ID', 'User', 'Amount', 'Status', 'Date'])
    
    for payment in payments:
        writer.writerow([
            payment.transaction_id,
            payment.user.email,
            payment.amount,
            payment.status,
            payment.created_at.date()
        ])
    
    writer.writerow([])
    writer.writerow(['Total Revenue', payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0])
    writer.writerow(['Total Transactions', payments.count()])
    
    # Class attendance summary
    writer.writerow([])
    writer.writerow(['Weekly Class Report'])
    writer.writerow(['Total Classes', sessions.count()])
    writer.writerow(['Completed', sessions.filter(status='completed').count()])
    writer.writerow(['Cancelled', sessions.filter(status='cancelled').count()])
    writer.writerow(['No Show', sessions.filter(status='no_show').count()])
    
    # Send report via email
    report_content = output.getvalue()
    send_mail(
        f'Weekly Report - {start_date} to {end_date}',
        'Please find the weekly report attached.',
        settings.DEFAULT_FROM_EMAIL,
        ['admin@amarquran.com'],
        fail_silently=False,
        html_message=f'<pre>{report_content}</pre>'
    )
    
    return True