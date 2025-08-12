from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import Payment, Invoice
from courses.models import Course, CourseEnrollment
import stripe
import json
from sslcommerz_lib import SSLCOMMERZ
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout(request, course_id):
    """Checkout page for course payment"""
    course = get_object_or_404(Course, id=course_id)
    
    if course.is_free:
        # Directly enroll in free courses
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'status': 'active'}
        )
        messages.success(request, _('Successfully enrolled in the course!'))
        return redirect('courses:detail', slug=course.slug)
    
    context = {
        'course': course,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'amount_bdt': course.current_price,
        'amount_usd': round(float(course.current_price) / 100, 2),  # Convert BDT to USD approx
    }
    return render(request, 'payments/checkout.html', context)


@login_required
def process_payment(request):
    """Process payment based on selected gateway"""
    if request.method != 'POST':
        return redirect('courses:list')
    
    course_id = request.POST.get('course_id')
    payment_method = request.POST.get('payment_method')
    course = get_object_or_404(Course, id=course_id)
    
    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        course=course,
        amount=course.current_price,
        currency='BDT',
        payment_method=payment_method,
        status='pending',
        description=f'Payment for {course.title}'
    )
    
    if payment_method == 'sslcommerz':
        return process_sslcommerz_payment(request, payment)
    elif payment_method == 'stripe':
        return process_stripe_payment(request, payment)
    else:
        messages.error(request, _('Invalid payment method'))
        return redirect('payments:checkout', course_id=course.id)


def process_sslcommerz_payment(request, payment):
    """Process payment through SSLCommerz"""
    
    sslcz_settings = {
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_pass': settings.SSLCOMMERZ_STORE_PASSWORD,
        'issandbox': settings.SSLCOMMERZ_SANDBOX
    }
    
    sslcz = SSLCOMMERZ(sslcz_settings)
    
    post_body = {
        'total_amount': float(payment.amount),
        'currency': payment.currency,
        'tran_id': str(payment.transaction_id),
        'success_url': request.build_absolute_uri('/payments/sslcommerz/success/'),
        'fail_url': request.build_absolute_uri('/payments/sslcommerz/fail/'),
        'cancel_url': request.build_absolute_uri('/payments/sslcommerz/cancel/'),
        'emi_option': 0,
        'cus_name': payment.user.get_full_name(),
        'cus_email': payment.user.email,
        'cus_phone': payment.user.phone_number,
        'cus_add1': payment.user.address or 'N/A',
        'cus_city': payment.user.city or 'Dhaka',
        'cus_country': payment.user.country or 'Bangladesh',
        'shipping_method': 'NO',
        'product_name': payment.course.title,
        'product_category': 'Online Course',
        'product_profile': 'general',
        'value_a': payment.id,  # Store payment ID for reference
    }
    
    response = sslcz.createSession(post_body)
    
    if response['status'] == 'SUCCESS':
        return redirect(response['GatewayPageURL'])
    else:
        logger.error(f"SSLCommerz payment initiation failed: {response}")
        messages.error(request, _('Payment initiation failed. Please try again.'))
        return redirect('payments:checkout', course_id=payment.course.id)


@csrf_exempt
def sslcommerz_success(request):
    """Handle successful SSLCommerz payment"""
    if request.method == 'POST':
        payment_data = request.POST.dict()
        tran_id = payment_data.get('tran_id')
        val_id = payment_data.get('val_id')
        amount = payment_data.get('amount')
        payment_id = payment_data.get('value_a')
        
        try:
            payment = Payment.objects.get(id=payment_id, transaction_id=tran_id)
            
            # Verify payment with SSLCommerz
            sslcz_settings = {
                'store_id': settings.SSLCOMMERZ_STORE_ID,
                'store_pass': settings.SSLCOMMERZ_STORE_PASSWORD,
                'issandbox': settings.SSLCOMMERZ_SANDBOX
            }
            sslcz = SSLCOMMERZ(sslcz_settings)
            
            validation_data = {
                'val_id': val_id,
                'store_id': settings.SSLCOMMERZ_STORE_ID,
                'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
            }
            
            response = sslcz.hash_validate(payment_data)
            
            if response:
                # Payment verified
                payment.status = 'completed'
                payment.gateway_transaction_id = val_id
                payment.gateway_response = payment_data
                payment.save()
                
                # Enroll student in course
                CourseEnrollment.objects.create(
                    student=payment.user,
                    course=payment.course,
                    status='active'
                )
                
                # Generate invoice
                generate_invoice(payment)
                
                messages.success(request, _('Payment successful! You are now enrolled in the course.'))
                return redirect('courses:detail', slug=payment.course.slug)
            else:
                payment.status = 'failed'
                payment.save()
                messages.error(request, _('Payment verification failed.'))
                
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for transaction: {tran_id}")
            messages.error(request, _('Payment record not found.'))
    
    return redirect('dashboard:home')


def process_stripe_payment(request, payment):
    """Process payment through Stripe"""
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': payment.course.title,
                        'description': payment.course.description[:200],
                    },
                    'unit_amount': int(float(payment.amount) * 100 / 100),  # Convert to cents and USD
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(f'/payments/stripe/success/?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment.id}'),
            cancel_url=request.build_absolute_uri(f'/payments/checkout/{payment.course.id}/'),
            metadata={
                'payment_id': payment.id,
                'user_id': payment.user.id,
                'course_id': payment.course.id,
            }
        )
        
        payment.gateway_transaction_id = checkout_session.id
        payment.save()
        
        return redirect(checkout_session.url, code=303)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        messages.error(request, _('Payment processing failed. Please try again.'))
        return redirect('payments:checkout', course_id=payment.course.id)


@login_required
def stripe_success(request):
    """Handle successful Stripe payment"""
    session_id = request.GET.get('session_id')
    payment_id = request.GET.get('payment_id')
    
    if not session_id or not payment_id:
        messages.error(request, _('Invalid payment session.'))
        return redirect('dashboard:home')
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Get payment record
        payment = Payment.objects.get(
            id=payment_id,
            gateway_transaction_id=session_id
        )
        
        if session.payment_status == 'paid':
            payment.status = 'completed'
            payment.gateway_response = session.to_dict()
            payment.save()
            
            # Enroll student in course
            CourseEnrollment.objects.get_or_create(
                student=payment.user,
                course=payment.course,
                defaults={'status': 'active'}
            )
            
            # Generate invoice
            generate_invoice(payment)
            
            messages.success(request, _('Payment successful! You are now enrolled in the course.'))
            return redirect('courses:detail', slug=payment.course.slug)
        else:
            payment.status = 'failed'
            payment.save()
            messages.error(request, _('Payment was not completed.'))
            
    except stripe.error.StripeError as e:
        logger.error(f"Stripe verification error: {str(e)}")
        messages.error(request, _('Payment verification failed.'))
    except Payment.DoesNotExist:
        messages.error(request, _('Payment record not found.'))
    
    return redirect('dashboard:home')


def generate_invoice(payment):
    """Generate PDF invoice for payment"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    from django.core.files.base import ContentFile
    from datetime import datetime
    
    # Create invoice record
    invoice = Invoice.objects.create(payment=payment)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#059669'),
        alignment=1  # Center
    )
    elements.append(Paragraph('INVOICE', title_style))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Company info
    company_info = """
    <para align=center>
    <b>Amar Quran</b><br/>
    Online Qur'an Learning Platform<br/>
    Email: info@amarquran.com<br/>
    Phone: +880 1XXX-XXXXXX
    </para>
    """
    elements.append(Paragraph(company_info, styles['Normal']))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Invoice details
    invoice_data = [
        ['Invoice Number:', payment.invoice_number],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Payment Method:', payment.get_payment_method_display()],
        ['Transaction ID:', str(payment.transaction_id)],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2 * inch, 4 * inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Customer info
    elements.append(Paragraph('<b>Bill To:</b>', styles['Normal']))
    customer_info = f"""
    {payment.user.get_full_name()}<br/>
    {payment.user.email}<br/>
    {payment.user.phone_number or 'N/A'}<br/>
    {payment.user.address or 'N/A'}
    """
    elements.append(Paragraph(customer_info, styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Items table
    items_data = [
        ['Description', 'Amount'],
        [payment.course.title, f'{payment.currency} {payment.amount}'],
    ]
    
    items_table = Table(items_data, colWidths=[4 * inch, 2 * inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Total
    total_data = [
        ['', 'Total:', f'{payment.currency} {payment.amount}'],
    ]
    total_table = Table(total_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 0), (2, 0), 14),
    ]))
    elements.append(total_table)
    
    # Footer
    elements.append(Spacer(1, 1 * inch))
    footer_text = """
    <para align=center fontSize=10>
    Thank you for choosing Amar Quran!<br/>
    This is a computer-generated invoice and does not require a signature.
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    # Save to invoice
    invoice.invoice_pdf.save(
        f'invoice_{payment.invoice_number}.pdf',
        ContentFile(pdf)
    )
    
    return invoice


@csrf_exempt
def sslcommerz_fail(request):
    """Handle failed SSLCommerz payment"""
    if request.method == 'POST':
        payment_data = request.POST.dict()
        payment_id = payment_data.get('value_a')
        
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = 'failed'
            payment.gateway_response = payment_data
            payment.save()
            
            messages.error(request, _('Payment failed. Please try again.'))
            return redirect('payments:checkout', course_id=payment.course.id)
            
        except Payment.DoesNotExist:
            messages.error(request, _('Payment record not found.'))
    
    return redirect('dashboard:home')


@csrf_exempt
def sslcommerz_cancel(request):
    """Handle cancelled SSLCommerz payment"""
    if request.method == 'POST':
        payment_data = request.POST.dict()
        payment_id = payment_data.get('value_a')
        
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = 'cancelled'
            payment.gateway_response = payment_data
            payment.save()
            
            messages.warning(request, _('Payment was cancelled.'))
            return redirect('payments:checkout', course_id=payment.course.id)
            
        except Payment.DoesNotExist:
            messages.error(request, _('Payment record not found.'))
    
    return redirect('dashboard:home')


@csrf_exempt
def sslcommerz_ipn(request):
    """Handle SSLCommerz IPN (Instant Payment Notification)"""
    if request.method == 'POST':
        # Log IPN data for debugging
        logger.info(f"SSLCommerz IPN received: {request.POST.dict()}")
        return HttpResponse('OK')
    return HttpResponse('Invalid request', status=400)


def stripe_cancel(request):
    """Handle cancelled Stripe payment"""
    messages.warning(request, _('Payment was cancelled.'))
    return redirect('courses:list')


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            # Handle successful payment
            payment_id = session['metadata'].get('payment_id')
            if payment_id:
                payment = Payment.objects.get(id=payment_id)
                payment.status = 'completed'
                payment.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def payment_history(request):
    """Display user's payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/history.html', {'payments': payments})


@login_required
def download_invoice(request, invoice_number):
    """Download invoice PDF"""
    try:
        invoice = Invoice.objects.get(
            invoice_number=invoice_number,
            payment__user=request.user
        )
        
        if invoice.invoice_pdf:
            response = HttpResponse(
                invoice.invoice_pdf.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
            return response
        else:
            messages.error(request, _('Invoice PDF not found.'))
            
    except Invoice.DoesNotExist:
        messages.error(request, _('Invoice not found.'))
    
    return redirect('payments:payment_history')