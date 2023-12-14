from rest_framework.routers import DefaultRouter
from creditapi.viewsets import CustomerViewSet, LoanViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'loans', LoanViewSet, basename='loan')




