from django.contrib.auth import get_user_model
from django.contrib.gis.geos import LineString, Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from spots_routes.models import Difficulty, Route, Spot, SpotStatusReview, TravelMode

User = get_user_model()

# GIF 1x1 válido: basta para pasar la validación de ImageField.
TINY_GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


def make_spot(user, status_key='APPROVED', name='Spot'):
    approved = status_key == 'APPROVED'
    return Spot.objects.create(
        user=user,
        name=name,
        description='desc',
        spot_thumbnail_path=SimpleUploadedFile('thumb.jpg', TINY_GIF, content_type='image/gif'),
        location=Point(-104.31, 19.05, srid=4326),
        status=SpotStatusReview.objects.get(key=status_key),
        is_active=approved,
    )


def make_route(user, spot):
    return Route.objects.create(
        user=user,
        spot=spot,
        difficulty=Difficulty.objects.get(key='EASY'),
        travel_mode=TravelMode.objects.get(key='WALKING'),
        path=LineString((-104.32, 19.04), (-104.31, 19.05), srid=4326),
    )


class SpotModerationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='owner', email='o@example.com', password='x')
        self.admin = User.objects.create_superuser(username='admin', email='a@example.com', password='x')
        self.pending = make_spot(self.user, 'PENDING', name='Pendiente')

    def test_my_spots_incluye_pendientes_con_estado(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/v1/spots/my_spots/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status_name'], self.pending.status.name)
        self.assertFalse(response.data[0]['is_active'])

    def test_listado_publico_oculta_pendientes(self):
        response = self.client.get('/api/v1/spots/')
        self.assertEqual(response.data['count'], 0)

    def test_admin_lista_y_autoriza_pendientes(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/v1/spots/', {'status': 'PENDING'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.post(f'/api/v1/spots/{self.pending.id}/authorize/')
        self.assertEqual(response.status_code, 200)
        self.pending.refresh_from_db()
        self.assertTrue(self.pending.is_active)

    def test_admin_rechaza_pendiente(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(f'/api/v1/spots/{self.pending.id}/deny/', {'reason': 'Duplicado'})
        self.assertEqual(response.status_code, 200)
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status.key, 'REJECTED')
        self.assertEqual(self.pending.reject_reason, 'Duplicado')


class RouteListingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='walker', email='w@example.com', password='x')
        self.other = User.objects.create_user(username='other', email='x@example.com', password='x')
        self.spot_a = make_spot(self.user, name='A')
        self.spot_b = make_spot(self.user, name='B')
        self.route_a = make_route(self.user, self.spot_a)
        self.route_b = make_route(self.other, self.spot_b)

    def test_rutas_anidadas_solo_del_spot(self):
        response = self.client.get(f'/api/v1/spots/{self.spot_a.id}/routes/')
        ids = [r['id'] for r in response.data['results']]
        self.assertEqual(ids, [self.route_a.id])

    def test_mis_rutas(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/v1/routes/mine/')
        self.assertEqual(response.status_code, 200)
        ids = [r['id'] for r in response.data['results']]
        self.assertEqual(ids, [self.route_a.id])

    def test_mis_rutas_requiere_auth(self):
        response = self.client.get('/api/v1/routes/mine/')
        self.assertEqual(response.status_code, 401)

    def test_catalogos_sembrados(self):
        self.assertTrue(Difficulty.objects.filter(key='EASY').exists())
        self.assertTrue(TravelMode.objects.filter(key='WALKING').exists())
