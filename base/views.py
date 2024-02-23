import calendar
import os
from datetime import date, timedelta
from datetime import datetime

import pdfplumber
import pdfreader
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, reverse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.views import generic

from .forms import OfferForm, UserForm, CalendarEventForm
from .models import Offer, CalendarEvent
from .utils import Calendar


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            User.objects.get(username=username)
        except Exception:
            messages.error(request, 'User does not exist!')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or password does not exist.')
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Registration error.')
    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    query = (
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(position__icontains=q) |
            Q(address__icontains=q) |
            Q(skills__icontains=q) |
            Q(education__icontains=q) |
            Q(experience__icontains=q) |
            Q(interests__icontains=q) |
            Q(status__icontains=q)
    )

    # only HR can see all offers
    if request.user.is_superuser:
        offers = Offer.objects.filter(query)
    else:
        # regular users should only see their own offers
        offers = Offer.objects.filter((query) & Q(user__id__exact=request.user.id))

    offer_count = offers.count()
    context = {'offers': offers, 'offer_count': offer_count}
    return render(request, 'base/home.html', context)


def offer(request, pk):
    offer = Offer.objects.get(id=pk)
    if offer.user == request.user or request.user.is_superuser:
        filename = request.GET.get('filename', '')
        if filename:
            path_to_file = os.path.join('uploads', 'cv', f'{filename}')
            opened_file = open(path_to_file, 'rb')
            response = HttpResponse(opened_file.read(), content_type="text/plain")
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(path_to_file)
            opened_file.close()
            return response
        offer_file_name = offer.file.name
        context = {'offer': offer, 'filename': offer_file_name}
        return render(request, 'base/offer.html', context)
    else:
        return HttpResponse('Permission denied.')


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    offers = user.offer_set.all()
    if offers:
        offer = offers[0]
    context = {'user': user, 'offers': offers, 'offer': offer}
    return render(request, 'base/profile.html', context)


@login_required(login_url='/login')
def createOffer(request):
    form = OfferForm()

    if request.method == 'POST':

        uploaded_file = request.FILES.get('uploaded_file')
        tmp_file_path = uploaded_file.temporary_file_path()
        fd = open(tmp_file_path, "rb")

        # read text
        pdfText = pdfplumber.open(fd)
        first_page = pdfText.pages[0]
        contents = {}
        if first_page:
            pdf_content = first_page.extract_text(x_tolerance=3, x_tolerance_ratio=None, y_tolerance=3, layout=False,
                                                  x_density=7.25, y_density=13).split('\n')
            for row in pdf_content:
                row_content = row.split(':')
                contents[row_content[0].lower()] = row_content[1][1:]

        # create offer object
        created_offer = Offer(
            user=request.user,
            name=contents.get('name', 'none'),
            email=contents.get('email', 'none'),
            position=contents.get('position', 'none'),
            address=contents.get('address', 'none'),
            skills=contents.get('skills', 'none'),
            education=contents.get('education', 'none'),
            experience=contents.get('experience', 'none'),
            interests=contents.get('interests', 'none'),
            file=uploaded_file)
        created_offer.save()

        # rename cv file
        cv_name = f'CV_{created_offer.id}'
        os.rename(created_offer.file.path, f'./uploads/cv/{cv_name}.pdf')
        created_offer.file.name = f'{cv_name}.pdf'

        # read image from CV
        pdfImg = pdfreader.SimplePDFViewer(fd)
        pdfImg.render()
        for canvas in pdfImg:
            image = list(canvas.images.values())
            if image:
                image = image[0]
                pil_image = image.to_Pillow()
                pil_image.save(f'./uploads/cv_images/{cv_name}.png')
                created_offer.picture.name = f'{cv_name}.png'

        created_offer.save()
        return redirect('home')
    context = {'form': form}
    return render(request, 'base/offer_form.html', context)


@login_required(login_url='/login')
def updateOffer(request, pk):
    offer = Offer.objects.get(id=pk)
    form = OfferForm(instance=offer)
    statuses = ['Pending', 'Accepted', 'Rejected']
    if not request.user.is_superuser:
        return HttpResponse('Permission denied.')

    if request.method == 'POST':
        offer.name = request.POST.get('name')
        offer.email = request.POST.get('email')
        offer.position = request.POST.get('position')
        offer.address = request.POST.get('address')
        offer.skills = request.POST.get('skills')
        offer.education = request.POST.get('education')
        offer.experience = request.POST.get('experience')
        offer.interests = request.POST.get('interests')
        status = request.POST.get('status')
        if status == 'Rejected':
            if offer.email:
                send_mail(
                    "Your application to JobOffers",
                    f"Hello {offer.name}. Your application for the position of {offer.position} for JobOffers has been rejected.",
                    "pjf.zaliczenie@gmail.com",
                    ["pjf.zaliczenie@gmail.com"],
                    fail_silently=False,
                )
        elif status == 'Accepted':
            if offer.email:
                send_mail(
                    "Your application to JobOffers",
                    f"Hello {offer.name}. Your application for the position of {offer.position} for JobOffers has been accepted.",
                    "pjf.zaliczenie@gmail.com",
                    ["pjf.zaliczenie@gmail.com"],
                    fail_silently=False,
                )
        offer.status = status
        offer.save()
        return redirect('home')
    context = {'form': form, 'offer': offer, 'statuses': statuses}
    return render(request, 'base/offer_form.html', context)


@login_required(login_url='/login')
def deleteOffer(request, pk):
    offer = Offer.objects.get(id=pk)

    if not request.user.is_superuser:
        return HttpResponse('Permission denied.')

    if request.method == 'POST':
        send_mail(
            "Your application to JobOffers",
            f"Hello {offer.name}. Your application for the position of {offer.position} for JobOffers has been rejected.",
            "pjf.zaliczenie@gmail.com",
            ["pjf.zaliczenie@gmail.com"],
            fail_silently=False,
        )
        offer.delete()
        if offer.file:
            os.remove(f'./uploads/cv/{offer.file.name}')
        if offer.picture:
            os.remove(f'./uploads/cv_images/{offer.picture.name}')
        return redirect('home')
    context = {'obj': offer}
    return render(request, 'base/delete.html', context)


@login_required(login_url='/login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    context = {'form': form}
    return render(request, 'base/update-user.html', context)


class CalendarView(generic.ListView):
    model = CalendarEvent
    template_name = 'base/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.GET:
            description = self.request.GET.get('q', '')
        else:
            description = ''

        # use today's date for the calendar
        d = get_date(self.request.GET.get('month', None))
        cal = Calendar(d.year, d.month)
        html_cal = cal.formatmonth(description, withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['prev_month'] = prev_month(d)
        context['next_month'] = next_month(d)

        return context


def get_date(req_month):
    if req_month:
        year, month = (int(x) for x in req_month.split('-'))
        return date(year, month, day=1)
    return datetime.today()


def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month


def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month


@login_required(login_url='/login')
def calendar_event(request, event_id=None):
    if event_id:
        instance = get_object_or_404(CalendarEvent, pk=event_id)
    else:
        instance = CalendarEvent()

    form = CalendarEventForm(request.POST or None, instance=instance)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('calendar'))
    return render(request, 'base/calendar_event.html', {'form': form, 'event_id': instance.pk})


@login_required(login_url='/login')
def calendar_event_delete(request, event_id=None):
    if event_id:
        instance = get_object_or_404(CalendarEvent, pk=event_id)
    else:
        instance = CalendarEvent()

    if request.method == 'POST':
        instance.delete()
        return redirect('calendar')
    return render(request, 'base/calendar_event_delete.html', {'event_id': instance.pk, 'event_name': instance.title})
