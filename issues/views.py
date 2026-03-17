from django.shortcuts import render
from .models import Issue

# Create your views here.

def issue_list(request): 
    issues = Issue.objects.all()
    return render(request, 'issues/issue_list.html', {'issues': issues})