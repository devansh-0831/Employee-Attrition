from django.urls import path
from . import views

urlpatterns = [
    path('', views.Dashboards, name='Dashboards'),
    path('AI_Prediction/', views.AI_Prediction, name='AI Prediction'),
    path('Dept_Trends/', views.Dept_Trends, name='Dept_Trends'),
    path('Employees/', views.Employees, name='Employees'),
    #for insert api
    path('Employee_data_insert/', views.Employee_data_insert, name='Employee_data_insert'),
    #for delete api
    path('Employee_data_delete/', views.Employee_data_delete, name='Employee_data_delete'),
    #for test api
    path('Test/', views.Test, name='test')
]