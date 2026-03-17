from django.shortcuts import render, redirect
from .models import Issue
from django.contrib.auth.models import User

# Create your views here.

def issue_list(request): 
    issues = Issue.objects.all()
    return render(request, 'issues/issue_list.html', {'issues': issues})

def issue_new(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        description = request.POST.get('description', '') #por si descripción vacía
        user = User.objects.get(id = 1) #por defecto, falta por configurar
        Issue.objects.create(subject = subject, description = description, created_by = user)
        return redirect('issue_list') #lo tengo en URLs
    return render(request, 'issues/issue_new.html') #si acaba de entrar a esa página(GET)

#no inicializo otros atrbiutos porque ya tienen valor por defecto de momento