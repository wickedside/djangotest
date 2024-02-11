from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from orders.models import Order


class OrdersAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpassword')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword',
            'category': 'testcategory'
        }

    def test_user_registration(self):
        response = self.client.post('/api/register/', self.user_data)
        print(response.content)  # Использую response.content для отладки
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_login(self):
        # Сначала зарегистрируем пользователя
        self.client.post('/api/register/', self.user_data)
        # Потом попытаемся войти
        response = self.client.post('/api/login/', {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        token = response.data['access']
        # Установим токен для последующих запросов
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

    def test_create_order(self):
        # Перед созданием заказа необходимо залогинить пользователя
        self.test_user_login()
        response = self.client.post('/api/orders/', self.order_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().title, self.order_data['title'])

    def test_list_orders_by_category(self):
        # Предполагается, что пользователь уже зарегистрирован и авторизован
        self.test_user_login()
        # Добавляем несколько заказов в базу данных
        Order.objects.create(title="Order 1", description="Description 1", category="testcategory", user=self.user)
        Order.objects.create(title="Order 2", description="Description 2", category="othercategory", user=self.user)
        Order.objects.create(title="Order 3", description="Description 3", category="testcategory", user=self.user)
        # Запрос к эндпоинту для получения списка заказов
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что в ответе только заказы, соответствующие категории пользователя
        orders_data = response.json()
        self.assertEqual(len(orders_data), 2)  # Только 2 заказа соответствуют категории 'testcategory'
        self.assertTrue(all(order['category'] == 'testcategory' for order in orders_data))

# Ну и т.д. для других тестов
