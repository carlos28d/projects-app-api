from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Project, Tag

from project.serializers import ProjectSerializer, ProjectDetailSerializer


PROJECTS_URL = reverse('project:project-list')


def detail_url(project_id):
    """Return project detail URL"""
    return reverse('project:project-detail', args=[project_id])


def sample_tag(user, name='Main project'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_project(user, **params):
    """Create and return a sample project"""
    defaults = {
        'title': 'Sample project',
        'description': 'This is a sample project',
        'price': 5.00,
    }
    defaults.update(params)

    return Project.objects.create(user=user, **defaults)


class PublicProjectApiTests(TestCase):
    """Test unauthenticated project API access"""

    def setUp(self):
        self.client = APIClient()

    def test_required_auth(self):
        """Test the authentication is required"""
        res = self.client.get(PROJECTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateProjectApiTests(TestCase):
    """Test authenticated project API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_projects(self):
        """Test retrieving list of projects"""
        sample_project(user=self.user)
        sample_project(user=self.user)

        res = self.client.get(PROJECTS_URL)

        projects = Project.objects.all().order_by('-id')
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_projects_limited_to_user(self):
        """Test retrieving projects for user"""
        user2 = get_user_model().objects.create_user(
            'other@gmail.com',
            'password123'
        )
        sample_project(user=user2)
        sample_project(user=self.user)

        res = self.client.get(PROJECTS_URL)

        projects = Project.objects.filter(user=self.user)
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_project_detail(self):
        """Test viewing a project detail"""
        project = sample_project(user=self.user)
        project.tags.add(sample_tag(user=self.user))

        url = detail_url(project.id)
        res = self.client.get(url)

        serializer = ProjectDetailSerializer(project)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_project(self):
        """Test creating project"""
        payload = {
            'title': 'Django Project',
            'description': 'A little Django project about projects',
            'price': 5.00
        }
        res = self.client.post(PROJECTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(project, key))

    def test_create_project_with_tags(self):
        """Test creating a project with tags"""
        tag1 = sample_tag(user=self.user, name='Internal')
        tag2 = sample_tag(user=self.user, name='External')
        payload = {
            'title': 'Videogame with Unreal Engine',
            'tags': [tag1.id, tag2.id],
            'description': 'A massive open world videogame',
            'price': 5.00
        }
        res = self.client.post(PROJECTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=res.data['id'])
        tags = project.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_parcial_update_recipe(self):
        """Test updating a recipe with patch"""
        project = sample_project(user=self.user)
        project.tags.add(sample_tag(user=self.user))
        project.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='External')

        payload = {'title': 'Django project', 'tags': [new_tag.id]}
        url = detail_url(project.id)
        self.client.patch(url, payload)

        project.refresh_from_db()
        self.assertEqual(project.title, payload['title'])
        tags = project.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_project(self):
        """Test updating a project with put"""
        project = sample_project(user=self.user)
        project.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Massive RPG',
            'description':
            'Massive RPG fantasy themed developed on FrostBite engine',
            'price': 5000
        }
        url = detail_url(project.id)
        self.client.put(url, payload)

        project.refresh_from_db()
        self.assertEqual(project.title, payload['title'])
        self.assertEqual(project.description, payload['description'])
        self.assertEqual(project.price, payload['price'])
        tags = project.tags.all()
        self.assertEqual(len(tags), 0)
