from django.shortcuts import render
from .models import EmployeeData,PredictionData
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import IntegerField
from django.db.models.functions import Cast
import joblib
pipeline=joblib.load('employee_attrition_model.joblib')

def Dashboards(request):
    #total_headcount
    Total_Headcount=EmployeeData.objects.all()
    Total_Headcount=len(Total_Headcount)

    #active employees
    Active_Employees=EmployeeData.objects.filter(Attrition='No').values('Attrition')
    Active_Employees=len(Active_Employees)

    #terminated
    Terminated=EmployeeData.objects.filter(Attrition='Yes').values('Attrition')
    Terminated=len(Terminated)

    #attrition rate
    Attrition_Rate=(Terminated/Active_Employees)*100
    Attrition_Rate=round(Attrition_Rate,2)

    #Attrition By Department
    dept_labels=EmployeeData.objects.all().values_list('JobRole',flat=True).distinct()
    dept_values=[]
    for i in dept_labels:  
        dept_values.append(EmployeeData.objects.filter(JobRole= i,Attrition='Yes').count())


    #gender distribution
    m_active=EmployeeData.objects.filter(Gender='Male',Attrition='No').count()
    m_term=EmployeeData.objects.filter(Gender='Male',Attrition='Yes' ).count()
    f_active=EmployeeData.objects.filter(Gender='Female',Attrition='No').count()
    f_term=EmployeeData.objects.filter(Gender='Female',Attrition='Yes').count()

    #Terminations and Activations by Year 
    years_at_company = list(EmployeeData.objects.all().annotate(years_int=Cast('YearsAtCompany',IntegerField())).values_list('years_int', flat=True).distinct().order_by('years_int'))

    active_year_values = []
    terminated_year_values = []

    for i in years_at_company:
        active_year_values.append(EmployeeData.objects.filter(YearsAtCompany=i, Attrition='No').count())
        terminated_year_values.append(EmployeeData.objects.filter(YearsAtCompany=i, Attrition='Yes').count())

    # termination and activation by age
    ages = list(EmployeeData.objects.annotate(Age1=Cast('Age', IntegerField())).order_by('Age1').values_list('Age1', flat=True).distinct())

    active_age_values = []
    terminated_age_values = []

    for age in ages:
        active_age_values.append(EmployeeData.objects.annotate(Age1=Cast('Age', IntegerField())).filter(Age1=age, Attrition='No').count())
        terminated_age_values.append(EmployeeData.objects.annotate(Age1=Cast('Age', IntegerField())).filter(Age1=age, Attrition='Yes').count())

        
        
    #dictionary
    context={'Total_Headcount':Total_Headcount,
             'Active_Employees':Active_Employees,
             'Terminated':Terminated,
             'Attrition_Rate':Attrition_Rate,
             'dept_labels':list(dept_labels),
             'dept_values':dept_values,
             'm_active':m_active,
             'm_term':m_term,
             'f_active':f_active,
             'f_term':f_term,
             'years_at_company':years_at_company,
             'active_year_values':active_year_values,
             'terminated_year_values':terminated_year_values,
             'age_labels': json.dumps(ages),
             'active_age_values': json.dumps(active_age_values),
             'terminated_age_values': json.dumps(terminated_age_values),
             }



    return render(request, 'Dashboards.html', context)

def AI_Prediction(request):
    prediction = None
    probability = None
    selected_values = None
    if request.method == 'POST':
        data_df = pd.DataFrame(request.POST.dict(), index=[0])
        data_df.drop(['csrfmiddlewaretoken'], axis=1, inplace=True)

        age = int(request.POST.get('age'))
        monthly_income = float(request.POST.get('monthly_income'))
        hourly_rate = float(request.POST.get('hourly_rate'))
        distance_from_home = int(request.POST.get('distance_from_home'))
        years_at_company = int(request.POST.get('years_at_company'))
        total_working_years = int(request.POST.get('total_working_years'))
        years_in_current_role = int(request.POST.get('years_in_current_role'))
        years_with_curr_manager = int(request.POST.get('years_with_curr_manager'))
        stock_option_level = int(request.POST.get('stock_option_level'))
        percent_salary_hike = int(request.POST.get('percent_salary_hike'))
        overtime = request.POST.get('overtime')
        job_role = request.POST.get('job_role')
        marital_status = request.POST.get('marital_status')

        daily_rate = hourly_rate * 8
        monthly_rate = daily_rate * 22

        data_df['Age'] = age
        data_df['MonthlyIncome'] = monthly_income
        data_df['HourlyRate'] = hourly_rate
        data_df['DistanceFromHome'] = distance_from_home
        data_df['YearsAtCompany'] = years_at_company
        data_df['TotalWorkingYears'] = total_working_years
        data_df['YearsInCurrentRole'] = years_in_current_role
        data_df['YearsWithCurrManager'] = years_with_curr_manager
        data_df['StockOptionLevel'] = stock_option_level
        data_df['PercentSalaryHike'] = percent_salary_hike
        data_df['OverTime'] = overtime
        data_df['JobRole'] = job_role
        data_df['MaritalStatus'] = marital_status
        data_df['DailyRate'] = daily_rate
        data_df['MonthlyRate'] = monthly_rate


        probability = pipeline.predict_proba(data_df)[0][1]
        
        print(pipeline.predict_proba(data_df)[0][1])

        if probability >= 0.25:
            prediction = 'High Risk'
        else:
            prediction = 'Low Risk'

        probability = round(probability * 100, 2)

        PredictionData.objects.create(Age=age, JobRole=job_role, MonthlyIncome=monthly_income, OverTime=overtime, Prediction=prediction, Probability=probability)
        selected_values = request.POST

    return render(request, 'AI_Prediction.html', {'prediction':prediction, 'probability':probability, 'selected_values':selected_values})

def Dept_Trends(request):
    trends=[]

    #this is the  function where we show the department wise attrition trends based on year at company
    year_filter = request.GET.get('year','')                #this is to take the input from the frontend

    #get different YearsAtCompany values
    years=EmployeeData.objects.values_list('YearsAtCompany',flat=True).distinct()
    years = sorted(years, key=int)
    

    #getting all the departments
    roles=EmployeeData.objects.values_list('JobRole',flat=True).distinct()   #this will give us list of all the departments

    #getting the trends 
    for role in roles:
        #get employee of this department
        dept_data=EmployeeData.objects.filter(JobRole=role)

        if year_filter:
            dept_data=dept_data.filter(YearsAtCompany=year_filter)

        #getting total records from this data 
        total_employees = dept_data.count()
        #Active employee out of total
        active_count=dept_data.filter(Attrition='No').count()
        #employee who left
        terminated_count=dept_data.filter(Attrition='Yes').count()

        #dept wise attrition percentage
        if total_employees > 0:
            attrition_rate = round((terminated_count / total_employees) * 100,2)
        else:
            attrition_rate = 0

        #srtoring department result in the dictionary
        trends.append({
            'department_name': role,
            'total_employees': total_employees,
            'active_count': active_count,
            'terminated_count': terminated_count,
            'attrition_rate': attrition_rate
        })



    return render(request,'Dept_Trends.html',{'trends':trends,'year':years,'year_filter':year_filter})

def Employees(request):
    status = request.GET.get('status','')
    search = request.GET.get('search','')

    predictions=EmployeeData.objects.all()

    if status:
        predictions= EmployeeData.objects.filter(Attrition=status)

    if search:
        predictions= EmployeeData.objects.filter(JobRole=search)  

    return render(request,'Employees.html',{'predictions':predictions, 'status_filter':status, 'search_query':search})

@csrf_exempt
def Employee_data_insert(request):

    df = pd.read_csv(r'F:\code projects\employee_prediction\ML_Models\EmployeeData.csv')

    for i, j in df.iterrows():
        EmployeeData.objects.create(
            Age=j['Age'],
            DailyRate=j['DailyRate'],
            Attrition=j['Attrition'],
            BusinessTravel=j['BusinessTravel'],
            Department=j['Department'],
            DistanceFromHome=j['DistanceFromHome'],
            Education=j['Education'],
            EducationField=j['EducationField'],
            EmployeeCount=j['EmployeeCount'],
            EmployeeNumber=j['EmployeeNumber'],
            EnvironmentSatisfaction=j['EnvironmentSatisfaction'],
            Gender=j['Gender'],
            HourlyRate=j['HourlyRate'],
            JobInvolvement=j['JobInvolvement'],
            JobLevel=j['JobLevel'],
            JobRole=j['JobRole'],
            JobSatisfaction=j['JobSatisfaction'],
            MaritalStatus=j['MaritalStatus'],
            MonthlyIncome=j['MonthlyIncome'],
            MonthlyRate=j['MonthlyRate'],
            NumCompaniesWorked=j['NumCompaniesWorked'],
            Over18=j['Over18'],
            OverTime=j['OverTime'],
            PercentSalaryHike=j['PercentSalaryHike'],
            PerformanceRating=j['PerformanceRating'],
            RelationshipSatisfaction=j['RelationshipSatisfaction'],
            StandardHours=j['StandardHours'],
            StockOptionLevel=j['StockOptionLevel'],
            TotalWorkingYears=j['TotalWorkingYears'],
            TrainingTimesLastYear=j['TrainingTimesLastYear'],
            WorkLifeBalance=j['WorkLifeBalance'],
            YearsAtCompany=j['YearsAtCompany'],
            YearsInCurrentRole=j['YearsInCurrentRole'],
            YearsSinceLastPromotion=j['YearsSinceLastPromotion'],
            YearsWithCurrManager=j['YearsWithCurrManager']
        )

    return JsonResponse({
        'message': 'Employee data inserted successfully'
    })



def Employee_data_delete(request):
    EmployeeData.objects.all().delete()

    return JsonResponse({
        'message': 'Employee data deleted successfully'
    })

@csrf_exempt
def Test(request):
    print(request.POST)
    return JsonResponse({'message':'successful'})
