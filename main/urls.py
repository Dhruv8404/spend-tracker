from django.urls import path
from .views import ExpenseListCreateView, SpendSummaryView, index_view, static_file_view


urlpatterns = [
    path("", index_view, name="index"),
    path("style.css", static_file_view, {"filename": "style.css"}),
    path("app.js", static_file_view, {"filename": "app.js"}),
    path("expenses/", ExpenseListCreateView.as_view(), name="expense-list-create"),
    path("summary/", SpendSummaryView.as_view(), name="spend-summary"),
]