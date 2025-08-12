from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from dashboard.views import generate_users_report, generate_payments_report
import os

class Command(BaseCommand):
    help = 'Generate weekly/monthly reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            default='week',
            help='Report period: week or month'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send report'
        )
    
    def handle(self, *args, **options):
        period = options['period']
        email = options.get('email')
        
        if period == 'week':
            date_from = timezone.now() - timedelta(days=7)
        else:
            date_from = timezone.now().replace(day=1)
        
        date_to = timezone.now()
        
        # Generate reports
        self.stdout.write('Generating reports...')
        
        # Users report
        users_report = generate_users_report(
            'excel',
            date_from.strftime('%Y-%m-%d'),
            date_to.strftime('%Y-%m-%d')
        )
        
        # Payments report
        payments_report = generate_payments_report(
            'excel',
            date_from.strftime('%Y-%m-%d'),
            date_to.strftime('%Y-%m-%d')
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Reports generated successfully for {period}')
        )
        
        if email:
            # Send email with reports
            from django.core.mail import EmailMessage
            
            subject = f'Amar Quran {period.title()}ly Report'
            message = f'Please find attached the {period}ly reports.'
            
            email_msg = EmailMessage(
                subject,
                message,
                'reports@amarquran.com',
                [email],
            )
            
            # Attach reports
            # email_msg.attach('users_report.xlsx', users_report.content, 'application/vnd.ms-excel')
            # email_msg.attach('payments_report.xlsx', payments_report.content, 'application/vnd.ms-excel')
            
            email_msg.send()
            
            self.stdout.write(
                self.style.SUCCESS(f'Reports sent to {email}')
            )