# views.py

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import  TimetableEntry, Topic, SubTopic, QuizResult, Profile, Question, Resource,Reattempt_Question
from django.contrib.auth.forms import AuthenticationForm
from random import sample

import json

def home(request):
    return render(request, 'myapp/home.html')
from django.shortcuts import render

def pomodoro_view(request):
    return render(request, 'myapp/pomodoro.html')

def study_schedule_view(request):
    timetable_entries = TimetableEntry.objects.filter(is_completed=False).order_by('deadline')
    weak_topics = Topic.objects.all()
    return render(request, 'study_schedule.html', {
        'timetable_entries': timetable_entries,
        'weak_topics': weak_topics
    })

def set_deadline_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        topic_id = data.get('topic_id')
        deadline = data.get('deadline')

        if topic_id and deadline:
            topic = get_object_or_404(Topic, id=topic_id)
            TimetableEntry.objects.create(topic=topic, deadline=deadline)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid data'})

def mark_completed_view(request, topic_id):
    if request.method == 'POST':
        entry = get_object_or_404(TimetableEntry, topic__id=topic_id, is_completed=False)
        entry.is_completed = True
        entry.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})



# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Profile

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'myapp/signup.html', {'error': 'Username already exists'})
        if User.objects.filter(email=email).exists():
            return render(request, 'myapp/signup.html', {'error': 'Email already exists'})
        
        if password1 == password2:
            user = User.objects.create_user(username=username, email=email, password=password1)
            Profile.objects.create(user=user)  # Create profile for the new user
            login(request, user)
            return redirect('select_topic')
        else:
            # Handle password mismatch
            return render(request, 'myapp/signup.html', {'error': 'Passwords do not match'})
    
    return render(request, 'myapp/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        # Check if user authentication is successful
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            # Handle invalid login
            return render(request, 'myapp/login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'myapp/login.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Profile, QuizResult, Resource
import json

@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)

    # Get completed topics from Profile
    completed_topics = profile.completed_topics.all()

    # Get weak topics from Profile
    weak_topics = profile.weak_topics.all()

    # Fetch progress data
    completed_results = QuizResult.objects.filter(user=request.user)
    progress_data = completed_results.values('score', 'date_taken')
    progress_dates = [entry['date_taken'].strftime('%Y-%m-%d') for entry in progress_data]
    progress_scores = [entry['score'] for entry in progress_data]


    # Fetch resources
    resources = Resource.objects.filter(sub_topic__in=profile.weak_topics.all())

    context = {
        'weak_topics': weak_topics,
        'completed_topics': completed_topics,
        'progress_dates': json.dumps(progress_dates),  # Convert lists to JSON strings
        'progress_scores': json.dumps(progress_scores),  # Convert lists to JSON strings
        'notifications': notifications,
        'resources': resources,
    }

    return render(request, 'myapp/dashboard.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Profile

@login_required
def achievements_page(request):
    profile = Profile.objects.get(user=request.user)
    
    # Fetch completed topics as achievements
    achievements = profile.completed_topics.all()

    context = {
        'achievements': achievements
    }
    
    return render(request, 'myapp/achievements.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Topic, SubTopic, Profile, QuizResult
import json

@login_required
def select_topic(request):
    if request.method == 'POST':
        selected_topic_id = request.POST.get('topic_id')
        if selected_topic_id:
            return redirect('main_quiz', topic_id=selected_topic_id)
    
    topics = Topic.objects.all()
    
    context = {
        'topics': topics,
    }
    
    return render(request, 'myapp/select_topic.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Topic, SubTopic, QuizResult, Profile, Question
from random import sample
from django.shortcuts import get_object_or_404, redirect, render

from random import sample
from django.shortcuts import get_object_or_404, redirect, render

@login_required
def main_quiz(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    subtopics = topic.subtopics.all()
    all_questions = Question.objects.filter(sub_topic__in=subtopics)

    # Initialize or retrieve random questions for the quiz session
    if 'quiz_questions' not in request.session or request.method != 'POST':
        questions = sample(list(all_questions), min(10, len(all_questions)))
        request.session['quiz_questions'] = [q.id for q in questions]  # Save IDs to session
        print(f"Randomly selected questions: {[q.id for q in questions]}")  # Debug statement
    else:
        question_ids = request.session['quiz_questions']
        questions = Question.objects.filter(id__in=question_ids)
        print(f"Loaded questions from session: {question_ids}")  # Debug statement

    if request.method == 'POST':
        correct_answers = 0
        weak_topics = []
        
        for question in questions:
            selected_answer = request.POST.get(f'question_{question.id}')
            if selected_answer == question.correct_answer:
                correct_answers += 1
            else:
                weak_topics.append(question.sub_topic)
        
        time_taken = request.POST.get('time_taken')
        weak_topics = list(set(weak_topics))  # Remove duplicates
        
        result = QuizResult.objects.create(
            user=request.user,
            score=correct_answers,
            time_taken=time_taken,
            sub_topic=subtopics.first()  # Assuming sub_topic here is for the first subtopic
        )
        result.weak_topics.set(weak_topics)
        result.save()
        
        profile = Profile.objects.get(user=request.user)
        profile.weak_topics.add(*weak_topics)
        profile.completed_topics.add(*subtopics)
        profile.save()
        
        # Clear session after quiz completion
        del request.session['quiz_questions']
        
        return redirect('result', result_id=result.id)
    
    context = {
        'topic': topic,
        'questions': questions,
    }
    return render(request, 'myapp/main_quiz.html', context)

@login_required
def reattempt_quiz(request, subtopic_id):
    profile = Profile.objects.get(user=request.user)
    subtopic = get_object_or_404(SubTopic, pk=subtopic_id)
    # Fetch questions for the specific subtopic
    questions = Reattempt_Question.objects.filter(sub_topic=subtopic)
    weak_topics = profile.weak_topics.all()  # Fetch user's current weak topics

    if request.method == 'POST':
        correct_answers = 0
        total_questions = len(questions)
        incorrect_topics = []

        for question in questions:
            selected_answer = request.POST.get(f'question_{question.id}')
            if selected_answer == question.correct_answer:
                correct_answers += 1
            else:
                incorrect_topics.append(question.sub_topic)

        # Calculate correct percentage after counting correct answers
        correctpercent = correct_answers / total_questions if total_questions > 0 else 0

        time_taken = request.POST.get('time_taken')
        incorrect_topics = list(set(incorrect_topics))  # Remove duplicates

        # Create the quiz result
        result = QuizResult.objects.create(
            user=request.user,
            sub_topic=subtopic,  # Pass the subtopic here
            score=correct_answers,
            time_taken=float(time_taken),
        )
        result.weak_topics.set(incorrect_topics)
        result.save()

        # Update user's weak topics and completed topics
        if correctpercent >= 0.75:
            # Remove from weak topics and add to completed topics
            profile.weak_topics.remove(subtopic)
            profile.completed_topics.add(subtopic)
        else:
            profile.weak_topics.add(subtopic)

        profile.save()
        

        # Check if result is saved and has a valid ID
        if result.id:
            return redirect('result', result_id=result.id)
        else:
            # Handle case if result was not saved properly
            return redirect('error_page') 

    context = {
        'questions': questions,
        'subtopic': subtopic,
    }
    return render(request, 'myapp/reattempt_quiz.html', context)


@login_required
def result(request, result_id):
    result = get_object_or_404(QuizResult, pk=result_id)
    weak_topics = result.weak_topics.all()
    username = request.user.username

    context = {
        'result': result,
        'weak_topics': weak_topics,
        'username': username,
    }

    return render(request, 'myapp/result.html', context)


@login_required
def resources(request):
    profile = Profile.objects.get(user=request.user)
    weak_topics = profile.weak_topics.all()
    resources = Resource.objects.filter(topic__in=weak_topics)
    return render(request, 'myapp/resources.html', {'resources': resources})

@login_required
def track_progress(request):
    profile = Profile.objects.get(user=request.user)
    progress_data = QuizResult.objects.filter(user=request.user).values('score', 'time_taken', 'date_taken')
    progress_dates = [entry['date_taken'].strftime('%Y-%m-%d') for entry in progress_data]
    progress_scores = [entry['score'] for entry in progress_data]
    return JsonResponse({'dates': progress_dates, 'scores': progress_scores})

def notifications(request):
    # Placeholder notifications for demonstration
    notifications = ["Complete your Algebra quiz!", "New resources added for Trigonometry."]
    return JsonResponse({'notifications': notifications})

def logout(request):
    logout(request)
    return redirect('home')
