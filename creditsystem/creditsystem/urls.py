
from django.contrib import admin
from django.urls import path,include
from .router import router
from creditapi.viewsets import LoanViewSet
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include(router.urls)),
    path('api/loans/view_loan/<int:pk>/', LoanViewSet.as_view({'get': 'view_loan'}), name='view-loan'),
    path('api/loans/view_loans/', LoanViewSet.as_view({'get': 'view_loans'}), name='view-loans'),
]
