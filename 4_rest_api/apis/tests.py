from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from apis.models import Classroom, School, Student, Teacher
from apis.serializers import TeacherSerializer


class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.client.force_authenticate(User.objects.create_user('tester'))
        self.client.credentials(HTTP_ACCEPT='application/json')

        self.school_a = School.objects.create(name='Alpha School', short_name='AS', address='Bangkok')
        self.school_b = School.objects.create(name='Beta School', short_name='BS', address='Chiang Mai')

        self.room_a1 = Classroom.objects.create(school=self.school_a, grade=1, room=1)
        self.room_a2 = Classroom.objects.create(school=self.school_a, grade=1, room=2)
        self.room_b1 = Classroom.objects.create(school=self.school_b, grade=2, room=1)

        self.teacher_john = Teacher.objects.create(school=self.school_a, first_name='John', last_name='Doe', gender='M')
        self.teacher_john.classrooms.set([self.room_a1, self.room_a2])
        self.teacher_jane = Teacher.objects.create(school=self.school_b, first_name='Jane', last_name='Smith', gender='F')
        self.teacher_jane.classrooms.set([self.room_b1])

        self.teacher_noroom = Teacher.objects.create(school=self.school_a, first_name='Nina', last_name='Free', gender='F')

        self.student_tom = Student.objects.create(first_name='Tom', last_name='Doe', gender='M', classroom=self.room_a1)
        self.student_amy = Student.objects.create(first_name='Amy', last_name='Lee', gender='F', classroom=self.room_a2)
        self.student_bob = Student.objects.create(first_name='Bob', last_name='Ray', gender='M', classroom=self.room_b1)

    def ids(self, response):
        return [item['id'] for item in response.data['results']]


class AuthTests(APITestCase):
    def test_requires_authentication(self):
        response = self.client.get('/api/v1/schools/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SchoolAPITests(BaseAPITestCase):
    url = '/api/v1/schools/'

    def test_create(self):
        response = self.client.post(self.url, {'name': 'Gamma', 'short_name': 'GS', 'address': 'Phuket'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(School.objects.filter(name='Gamma').exists())

    def test_list_filter_by_name(self):
        response = self.client.get(self.url, {'name': 'alpha'})
        self.assertEqual(self.ids(response), [self.school_a.id])

    def test_detail_has_counts(self):
        response = self.client.get(f'{self.url}{self.school_a.id}/')
        self.assertEqual(response.data['classroom_count'], 2)
        self.assertEqual(response.data['teacher_count'], 2)  # John (2 rooms, counted once) + Nina (no room)
        self.assertEqual(response.data['student_count'], 2)

    def test_update(self):
        response = self.client.patch(f'{self.url}{self.school_a.id}/', {'name': 'Alpha New'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school_a.refresh_from_db()
        self.assertEqual(self.school_a.name, 'Alpha New')

    def test_delete(self):
        empty = School.objects.create(name='Empty', short_name='E', address='-')
        Classroom.objects.create(school=empty, grade=1, room=1)
        response = self.client.delete(f'{self.url}{empty.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(School.objects.filter(id=empty.id).exists())
        self.assertFalse(Classroom.objects.filter(school_id=empty.id).exists())

    def test_delete_with_students_rejected(self):
        response = self.client.delete(f'{self.url}{self.school_b.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Student.objects.filter(id=self.student_bob.id).exists())


class ClassroomAPITests(BaseAPITestCase):
    url = '/api/v1/classrooms/'

    def test_create(self):
        response = self.client.post(self.url, {'school': self.school_b.id, 'grade': 3, 'room': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_duplicate_rejected(self):
        response = self.client.post(self.url, {'school': self.school_a.id, 'grade': 1, 'room': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_filter_by_school(self):
        response = self.client.get(self.url, {'school': self.school_a.id})
        self.assertEqual(self.ids(response), [self.room_a1.id, self.room_a2.id])

    def test_detail_has_teachers_and_students(self):
        response = self.client.get(f'{self.url}{self.room_a1.id}/')
        self.assertEqual([t['id'] for t in response.data['teachers']], [self.teacher_john.id])
        self.assertEqual([s['id'] for s in response.data['students']], [self.student_tom.id])

    def test_update(self):
        response = self.client.patch(f'{self.url}{self.room_a2.id}/', {'room': 9}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.room_a2.refresh_from_db()
        self.assertEqual(self.room_a2.room, 9)

    def test_update_school_rejected(self):
        response = self.client.patch(f'{self.url}{self.room_a1.id}/', {'school': self.school_b.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.room_a1.refresh_from_db()
        self.assertEqual(self.room_a1.school, self.school_a)

    def test_update_same_school_allowed(self):
        payload = {'school': self.school_a.id, 'grade': 1, 'room': 5}
        response = self.client.put(f'{self.url}{self.room_a1.id}/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete(self):
        empty_room = Classroom.objects.create(school=self.school_a, grade=6, room=1)
        response = self.client.delete(f'{self.url}{empty_room.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Classroom.objects.filter(id=empty_room.id).exists())

    def test_delete_with_students_rejected(self):
        response = self.client.delete(f'{self.url}{self.room_a2.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Student.objects.filter(id=self.student_amy.id).exists())

    def test_str_does_not_query_school_per_row(self):
        with self.assertNumQueries(1):
            [str(classroom) for classroom in Classroom.objects.all()]


class TeacherAPITests(BaseAPITestCase):
    url = '/api/v1/teachers/'

    def test_create_with_classrooms(self):
        payload = {'school': self.school_a.id, 'first_name': 'Ann', 'last_name': 'Kim', 'gender': 'F',
                   'classrooms': [self.room_a1.id, self.room_a2.id]}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        teacher = Teacher.objects.get(id=response.data['id'])
        self.assertEqual(set(teacher.classrooms.values_list('id', flat=True)), {self.room_a1.id, self.room_a2.id})

    def test_create_without_classrooms(self):
        payload = {'school': self.school_a.id, 'first_name': 'Ann', 'last_name': 'Kim', 'gender': 'F'}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_classroom_of_other_school_rejected(self):
        payload = {'school': self.school_a.id, 'first_name': 'Ann', 'last_name': 'Kim', 'gender': 'F',
                   'classrooms': [self.room_b1.id]}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('classrooms', response.data)

    def test_update_school_only_rejected_when_classrooms_mismatch(self):
        response = self.client.patch(f'{self.url}{self.teacher_john.id}/', {'school': self.school_b.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_gender_rejected(self):
        response = self.client.post(self.url, {'school': self.school_a.id, 'first_name': 'X', 'last_name': 'Y', 'gender': 'Z'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_without_school_does_not_crash(self):
        serializer = TeacherSerializer(data={'first_name': 'X'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_list_filters(self):
        cases = [
            ({'school': self.school_a.id}, [self.teacher_john.id, self.teacher_noroom.id]),
            ({'classroom': self.room_b1.id}, [self.teacher_jane.id]),
            ({'first_name': 'jo'}, [self.teacher_john.id]),
            ({'last_name': 'smi'}, [self.teacher_jane.id]),
            ({'gender': 'F'}, [self.teacher_jane.id, self.teacher_noroom.id]),
            ({'classroom': self.room_a1.id}, [self.teacher_john.id]),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                self.assertEqual(self.ids(self.client.get(self.url, params)), expected)

    def test_detail_has_classrooms(self):
        response = self.client.get(f'{self.url}{self.teacher_john.id}/')
        self.assertEqual([c['id'] for c in response.data['classrooms']], [self.room_a1.id, self.room_a2.id])

    def test_update(self):
        payload = {'school': self.school_b.id, 'classrooms': [self.room_b1.id]}
        response = self.client.patch(f'{self.url}{self.teacher_john.id}/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.teacher_john.refresh_from_db()
        self.assertEqual(self.teacher_john.school, self.school_b)
        self.assertEqual(list(self.teacher_john.classrooms.values_list('id', flat=True)), [self.room_b1.id])

    def test_delete(self):
        response = self.client.delete(f'{self.url}{self.teacher_jane.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Teacher.objects.filter(id=self.teacher_jane.id).exists())


class StudentAPITests(BaseAPITestCase):
    url = '/api/v1/students/'

    def test_create(self):
        payload = {'first_name': 'Kai', 'last_name': 'Wong', 'gender': 'M', 'classroom': self.room_b1.id}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_without_classroom_rejected(self):
        response = self.client.post(self.url, {'first_name': 'X', 'last_name': 'Y', 'gender': 'M'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_filters(self):
        cases = [
            ({'school': self.school_a.id}, [self.student_tom.id, self.student_amy.id]),
            ({'classroom': self.room_b1.id}, [self.student_bob.id]),
            ({'first_name': 'am'}, [self.student_amy.id]),
            ({'last_name': 'doe'}, [self.student_tom.id]),
            ({'gender': 'M'}, [self.student_tom.id, self.student_bob.id]),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                self.assertEqual(self.ids(self.client.get(self.url, params)), expected)

    def test_detail_has_classroom(self):
        response = self.client.get(f'{self.url}{self.student_tom.id}/')
        self.assertEqual(response.data['classroom']['id'], self.room_a1.id)

    def test_update(self):
        response = self.client.patch(f'{self.url}{self.student_tom.id}/', {'classroom': self.room_a2.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_tom.refresh_from_db()
        self.assertEqual(self.student_tom.classroom, self.room_a2)

    def test_delete(self):
        response = self.client.delete(f'{self.url}{self.student_bob.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Student.objects.filter(id=self.student_bob.id).exists())


class PaginationTests(BaseAPITestCase):
    def test_list_is_paginated(self):
        School.objects.bulk_create(School(name=f'S{i}', short_name=f'S{i}', address='-') for i in range(25))
        first = self.client.get('/api/v1/schools/')
        self.assertEqual(first.data['count'], 27)
        self.assertEqual(len(first.data['results']), 20)
        self.assertIsNotNone(first.data['next'])
        second = self.client.get('/api/v1/schools/', {'page': 2})
        self.assertEqual(len(second.data['results']), 7)
        self.assertIsNone(second.data['next'])
