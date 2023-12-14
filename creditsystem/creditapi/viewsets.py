from rest_framework import viewsets,status
from django.db.models import Sum
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from rest_framework.decorators import action
from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanSerializer
from rest_framework.response import Response

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    @action(detail=False,methods=['POST'])
    def register(self,request):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers=self.get_success_headers(serializer.data)
        return Response(serializer.data,status=201,headers=headers)
    
    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False,methods=['POST'])
    def bulk_register(self, request):
        file = request.data.get('file')

        if not file or not file.name.endswith('.xls'):
            return Response({'error': 'Invalid file format. Please provide a valid XLS file.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file)
            customers_data = df.to_dict(orient='records')
            serializer = CustomerSerializer(data=customers_data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'success': 'Data inserted successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=False, methods=['post'])
    def bulk_insert(self, request):
        file = request.data.get('file')

        if not file or not file.name.endswith('.xls'):
            return Response({'error': 'Invalid file format. Please provide a valid XLS file.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file)
            loans_data = df.to_dict(orient='records')
            serializer = LoanSerializer(data=loans_data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'success': 'Data inserted successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['get'])
    def view_loan(self, request, pk=None):
        try:
            loan = self.get_object()
            serializer = self.get_serializer(loan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def view_loans(self, request):
        customer_id = request.query_params.get('customer_id')

        if not customer_id:
            return Response({'error': 'Customer ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            loans = Loan.objects.filter(customer_id=customer_id)
            serializer = self.get_serializer(loans, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def check_eligibility(self, request):
        customer_id = request.data.get('customer_id')
        loan_amount = request.data.get('loan_amount')
        interest_rate = request.data.get('interest_rate')
        tenure = request.data.get('tenure')

        if not all([customer_id, loan_amount, interest_rate, tenure]):
            return Response({'error': 'Incomplete data in the request'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        credit_score = self.calculate_credit_score(customer)

        
        if credit_score > 50:
            approved = True
            corrected_interest_rate = interest_rate  
        elif 50 >= credit_score > 30:
            approved = True
            corrected_interest_rate = max(12, interest_rate)  
        elif 30 >= credit_score > 10:
            approved = True
            corrected_interest_rate = max(16, interest_rate)  
        else:
            approved = False
            corrected_interest_rate = 0

        
        total_emis = Loan.objects.filter(customer_id=customer_id).exclude(loan_id=request.data.get('loan_id')).aggregate(Sum('monthly_repayment'))['monthly_repayment__sum'] or 0

        monthly_salary = customer.monthly_salary
        if total_emis > Decimal('0.5') * monthly_salary:
            approved = False
            corrected_interest_rate = 0

        
        monthly_installment = self.calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure)

        return Response({
            'customer_id': customer_id,
            'approval': approved,
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': monthly_installment
        }, status=status.HTTP_200_OK)

    def calculate_credit_score(self, customer):
        
        num_loans_taken = customer.loan_set.count()
        credit_score = min(100, num_loans_taken * 10)  

        return credit_score

    def calculate_monthly_installment(self, loan_amount, interest_rate, tenure):
        
        monthly_interest_rate = interest_rate / 1200

        if monthly_interest_rate == 0:
    
            monthly_installment = 0
        else:
            monthly_installment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -tenure)
        return monthly_installment
    
    @action(detail=False, methods=['post'])
    def create_loan(self, request):
        customer_id = request.data.get('customer_id')
        loan_amount = request.data.get('loan_amount')
        interest_rate = request.data.get('interest_rate')
        tenure = request.data.get('tenure')

        if not all([customer_id, loan_amount, interest_rate, tenure]):
            return Response({'error': 'Incomplete data in the request'}, status=status.HTTP_400_BAD_REQUEST)

        approved, corrected_interest_rate, message = self.check_eligibile(customer_id)

        if approved:
            total_emis = Loan.objects.filter(customer_id=customer_id).aggregate(Sum('monthly_repayment'))['monthly_repayment__sum'] or 0
            monthly_salary = Customer.objects.get(pk=customer_id).monthly_salary

            if total_emis > Decimal(0.5) * monthly_salary:
                approved = False
                corrected_interest_rate = 0
                message = "Loan not approved due to high EMIs"
            else:
                monthly_installment = self.calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure)
            start_date = datetime.now().date()
            
            end_date = start_date + timedelta(days=30 * tenure)

            loan_data = {
                'customer': customer_id,
                'loan_id': 566,
                'loan_amount': loan_amount,
                'interest_rate': corrected_interest_rate,
                'tenure': tenure,
                'monthly_repayment': monthly_installment,
                'start_date': start_date,
                'end_date': end_date,
                'emis_paid_on_time': 0,
            }

            serializer = LoanSerializer(data=loan_data)
            if serializer.is_valid():
                serializer.save()
                loan_id = serializer.data['loan_id']
            else:
                loan_id = None
                approved = False
                message = "Error creating loan"
        else:
            loan_id = None

        return Response({
            'loan_id': loan_id,
            'customer_id': customer_id,
            'loan_approved': approved,
            'message': message,
            'monthly_installment': monthly_installment if approved else None
        }, status=status.HTTP_200_OK)
    
    def check_eligibile(self, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return False, 0, "Customer not found"

        credit_score = self.calculate_credit_score(customer)

        if credit_score > 50:
            return True, 0, "Loan approved"
        elif 50 >= credit_score > 30:
            return True, 12, "Loan approved with interest rate > 12%"
        elif 30 >= credit_score > 10:
            return True, 16, "Loan approved with interest rate > 16%"
        else:
            return False, 0, "Loan not approved"
