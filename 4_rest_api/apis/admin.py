from django.contrib import admin

from apis.models import Classroom, School, Student, Teacher

admin.site.register([School, Classroom, Teacher, Student])
