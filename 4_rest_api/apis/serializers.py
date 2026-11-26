from rest_framework import serializers

from apis.models import Classroom, School, Student, Teacher


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name', 'short_name', 'address']


class SchoolDetailSerializer(SchoolSerializer):
    classroom_count = serializers.IntegerField(read_only=True)
    teacher_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)

    class Meta(SchoolSerializer.Meta):
        fields = SchoolSerializer.Meta.fields + ['classroom_count', 'teacher_count', 'student_count']


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'school', 'grade', 'room']

    def validate_school(self, school):
        if self.instance and school != self.instance.school:
            raise serializers.ValidationError('Cannot move a classroom to another school.')
        return school


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'school', 'first_name', 'last_name', 'gender', 'classrooms']

    def validate(self, attrs):
        school = attrs.get('school') or getattr(self.instance, 'school', None)
        if school is None:
            return attrs
        if 'classrooms' in attrs:
            classrooms = attrs['classrooms']
        else:
            classrooms = self.instance.classrooms.all() if self.instance else []
        if any(classroom.school_id != school.id for classroom in classrooms):
            raise serializers.ValidationError({'classrooms': 'All classrooms must belong to the teacher\'s school.'})
        return attrs


class TeacherSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'school', 'first_name', 'last_name', 'gender']


class TeacherDetailSerializer(TeacherSummarySerializer):
    classrooms = ClassroomSerializer(many=True, read_only=True)

    class Meta(TeacherSummarySerializer.Meta):
        fields = TeacherSummarySerializer.Meta.fields + ['classrooms']


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'gender', 'classroom']


class StudentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'gender']


class StudentDetailSerializer(StudentSummarySerializer):
    classroom = ClassroomSerializer(read_only=True)

    class Meta(StudentSummarySerializer.Meta):
        fields = StudentSummarySerializer.Meta.fields + ['classroom']


class ClassroomDetailSerializer(ClassroomSerializer):
    teachers = TeacherSummarySerializer(many=True, read_only=True)
    students = StudentSummarySerializer(many=True, read_only=True)

    class Meta(ClassroomSerializer.Meta):
        fields = ClassroomSerializer.Meta.fields + ['teachers', 'students']
