from django_filters import FilterSet, filters

from apis.models import Classroom, School, Student, Teacher


class SchoolFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = School
        fields = ['name']


class ClassroomFilter(FilterSet):
    class Meta:
        model = Classroom
        fields = ['school']


class TeacherFilter(FilterSet):
    classroom = filters.NumberFilter(field_name='classrooms', distinct=True)
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Teacher
        fields = ['school', 'classroom', 'first_name', 'last_name', 'gender']


class StudentFilter(FilterSet):
    school = filters.NumberFilter(field_name='classroom__school')
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Student
        fields = ['school', 'classroom', 'first_name', 'last_name', 'gender']
