from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Offer(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.TextField(null=True, blank=True, default='none')
    email = models.TextField(null=True, blank=True, default='none')
    position = models.TextField(null=True, blank=True, default='none')
    address = models.TextField(null=True, blank=True, default='none')
    skills = models.TextField(null=True, blank=True, default='none')
    education = models.TextField(null=True, blank=True, default='none')
    experience = models.TextField(null=True, blank=True, default='none')
    interests = models.TextField(null=True, blank=True, default='none')
    status = models.TextField(default='Pending')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    picture = models.FileField(upload_to='./uploads/cv_images', null=True, blank=True)
    file = models.FileField(upload_to='./uploads/cv')

    class Meta:
        ordering = ['-updated', 'created']

    def __str__(self):
        return self.name


class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    @property
    def get_html_url(self):
        url = reverse('calendar_event_edit', args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'
