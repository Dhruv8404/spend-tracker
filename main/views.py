import os
from datetime import date
from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Expense
from .serializers import ExpenseSerializer


def index_view(request):
    """
    Renders the frontend HTML app.
    """
    return render(request, "index.html")


def static_file_view(request, filename):
    """
    Serves static files (style.css, app.js) directly from frontend folder for root access.
    """
    filepath = settings.BASE_DIR / "frontend" / filename
    if os.path.exists(filepath):
        mime_types = {
            ".css": "text/css",
            ".js": "application/javascript",
            ".html": "text/html",
        }
        ext = os.path.splitext(filename)[1].lower()
        content_type = mime_types.get(ext, "text/plain")
        with open(filepath, "rb") as f:
            return HttpResponse(f.read(), content_type=content_type)
    raise Http404("File not found")


@method_decorator(csrf_exempt, name='dispatch')
class ExpenseListCreateView(APIView):
    """
    GET  /api/expenses/  - List expenses, sorted newest date first. Optional filters: category, start_date, end_date
    POST /api/expenses/  - Create a new expense
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        expenses = Expense.objects.all().order_by("-date", "-id")

        category = request.query_params.get("category")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if category and category.strip():
            expenses = expenses.filter(category__iexact=category.strip())

        if start_date:
            expenses = expenses.filter(date__gte=start_date)

        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)

        if serializer.is_valid():
            expense = serializer.save()
            return Response(
                ExpenseSerializer(expense).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@method_decorator(csrf_exempt, name='dispatch')
class SpendSummaryView(APIView):
    """
    GET /api/summary/ - Total spend, spend by category, month-over-month change & >20% increase insights
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        today = date.today()

        year_param = request.query_params.get("year")
        month_param = request.query_params.get("month")

        try:
            curr_year = int(year_param) if year_param else today.year
            curr_month = int(month_param) if month_param else today.month
        except ValueError:
            curr_year = today.year
            curr_month = today.month

        if curr_month == 1:
            prev_year = curr_year - 1
            prev_month = 12
        else:
            prev_year = curr_year
            prev_month = curr_month - 1

        total_aggregate = Expense.objects.aggregate(total=Sum('amount'))
        total_spend = float(total_aggregate['total'] or 0.0)

        category_qs = Expense.objects.values('category').annotate(total=Sum('amount')).order_by('-total')
        spend_by_category = {
            item['category']: round(float(item['total']), 2) for item in category_qs
        }

        curr_month_qs = Expense.objects.filter(
            date__year=curr_year,
            date__month=curr_month
        )
        curr_month_aggregate = curr_month_qs.aggregate(total=Sum('amount'))
        curr_month_spend = float(curr_month_aggregate['total'] or 0.0)

        prev_month_qs = Expense.objects.filter(
            date__year=prev_year,
            date__month=prev_month
        )
        prev_month_aggregate = prev_month_qs.aggregate(total=Sum('amount'))
        prev_month_spend = float(prev_month_aggregate['total'] or 0.0)

        mom_diff = round(curr_month_spend - prev_month_spend, 2)
        if prev_month_spend > 0:
            mom_percentage = round(((curr_month_spend - prev_month_spend) / prev_month_spend) * 100, 2)
        elif curr_month_spend > 0:
            mom_percentage = 100.0
        else:
            mom_percentage = 0.0

        curr_cat_qs = curr_month_qs.values('category').annotate(total=Sum('amount'))
        curr_cat_spend = {item['category'].lower(): (item['category'], float(item['total'])) for item in curr_cat_qs}

        prev_cat_qs = prev_month_qs.values('category').annotate(total=Sum('amount'))
        prev_cat_spend = {item['category'].lower(): float(item['total']) for item in prev_cat_qs}

        insights = []
        for cat_lower, (orig_cat_name, c_amount) in curr_cat_spend.items():
            p_amount = prev_cat_spend.get(cat_lower, 0.0)
            if p_amount > 0:
                pct_increase = round(((c_amount - p_amount) / p_amount) * 100, 2)
                if pct_increase > 20.0:
                    pct_str = f"{int(pct_increase)}" if pct_increase.is_integer() else f"{pct_increase}"
                    insights.append({
                        "category": orig_cat_name,
                        "previous_month_spend": round(p_amount, 2),
                        "current_month_spend": round(c_amount, 2),
                        "increase_percentage": pct_increase,
                        "message": f"{orig_cat_name} spend increased by {pct_str}% compared to previous month."
                    })

        summary_data = {
            "total_spend": round(total_spend, 2),
            "spend_by_category": spend_by_category,
            "current_month": {
                "year": curr_year,
                "month": curr_month,
                "total_spend": round(curr_month_spend, 2)
            },
            "previous_month": {
                "year": prev_year,
                "month": prev_month,
                "total_spend": round(prev_month_spend, 2)
            },
            "mom_change": {
                "difference": mom_diff,
                "percentage": mom_percentage,
            },
            "insights": insights
        }

        return Response(summary_data, status=status.HTTP_200_OK)