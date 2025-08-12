from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Checkout
    path('checkout/<int:course_id>/', views.checkout, name='checkout'),
    
    # Process payment
    path('process/', views.process_payment, name='process_payment'),
    
    # SSLCommerz callbacks
    path('sslcommerz/success/', views.sslcommerz_success, name='sslcommerz_success'),
    path('sslcommerz/fail/', views.sslcommerz_fail, name='sslcommerz_fail'),
    path('sslcommerz/cancel/', views.sslcommerz_cancel, name='sslcommerz_cancel'),
    path('sslcommerz/ipn/', views.sslcommerz_ipn, name='sslcommerz_ipn'),
    
    # Stripe callbacks
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Payment history
    path('history/', views.payment_history, name='payment_history'),
    path('invoice/<str:invoice_number>/', views.download_invoice, name='download_invoice'),
]