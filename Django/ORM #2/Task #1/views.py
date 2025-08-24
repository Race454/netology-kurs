from django.shortcuts import render
from .models import Student

def student_list(request):
    students = Student.objects.prefetch_related('teachers').all()
    return render(request, 'students_list.html', {'students': students})