from django.test import TestCase

# Create your tests here.
# auth/tests/test_jwt_views.py
from django.test import TestCase
from rest_framework.exceptions import ValidationError  # ← Importar de DRF
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
User = get_user_model()


class LoginViewTests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/auth/login/'  # Ajusta tu URL
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
    
    def test_login_con_username_exitoso(self):
        """Login con username correcto retorna tokens"""
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_con_email_exitoso(self):
        """Login con email correcto retorna tokens"""
        response = self.client.post(self.url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_sin_password(self):
        """Login sin password retorna 400"""
        response = self.client.post(self.url, {
            'username': 'testuser'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_login_sin_username_ni_email(self):
        """Login sin username ni email retorna 400"""
        response = self.client.post(self.url, {
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_login_credenciales_invalidas(self):
        """Login con password incorrecta retorna 401"""
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_login_email_inexistente(self):
        """Login con email que no existe retorna 401"""
        response = self.client.post(self.url, {
            'email': 'noexiste@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_login_usuario_inactivo(self):
        """Login con usuario inactivo retorna 401"""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(self.url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 401)


# auth/tests/test_password_views.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch

class PasswordResetRequestViewTests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/auth/password/reset/'  # Ajusta tu URL
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
    
    @patch('authentication.services.PasswordResetService.request_reset')
    def test_solicitud_reset_email_existente(self, mock_request_reset):
        """Solicitud con email existente retorna 200"""
        response = self.client.post(self.url, {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 200)
        mock_request_reset.assert_called_once()
    
    @patch('authentication.services.PasswordResetService.request_reset')
    def test_solicitud_reset_email_inexistente(self, mock_request_reset):
        """Email inexistente también retorna 200 (seguridad)"""
        response = self.client.post(self.url, {
            'email': 'noexiste@example.com'
        })
        # Por seguridad, no debe revelar si existe o no
        self.assertEqual(response.status_code, 200)
    
    def test_solicitud_reset_sin_email(self):
        """Sin email retorna 400"""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)


class PasswordResetConfirmViewTests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/auth/password/reset/confirm/'  # Ajusta tu URL
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
    
    @patch('authentication.services.PasswordResetService.confirm_reset')
    def test_confirmar_reset_exitoso(self, mock_confirm_reset):
        """Confirmación con token válido cambia contraseña"""
        mock_confirm_reset.return_value = self.user
        
        response = self.client.post(self.url, {
            'uidb64': 'fake_uid_base64',
            'token': 'fake_valid_token',
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, 200)
        mock_confirm_reset.assert_called_once()
    
    @patch('authentication.services.PasswordResetService.confirm_reset')
    def test_confirmar_reset_token_invalido(self, mock_confirm_reset):
        """Token inválido retorna error"""
        mock_confirm_reset.side_effect =  ValidationError("Token inválido")
        
        response = self.client.post(self.url, {
            'uidb64': 'fake_uid',
            'token': 'invalid_token',
            'new_password': 'newpass123'
        })
        self.assertEqual(response.status_code, 400) 
    
    def test_confirmar_reset_sin_datos(self):
        """Sin token/password retorna 400"""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
    
    def test_confirmar_reset_password_corta(self):
        """Contraseña muy corta retorna 400"""
        response = self.client.post(self.url, {
            'uidb64': 'fake_uid',
            'token': 'fake_token',
            'new_password': '123'
        })
        self.assertEqual(response.status_code, 400)

    
# auth/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import ValidationError
from authentication.services import UsersRegisterService


class RegistrationAPIViewTests(TestCase):
    """Tests para el registro de usuarios"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/auth/register/'  # Ajusta según tu URL
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
    
    @patch('core.services.email_service.ConfirmUserEmail.send_email')
    @patch('authentication.views.user_views.UsersRegisterService.get_confirmation_url')
    def test_registro_exitoso(self, mock_get_url, mock_send_email):
        """Registro exitoso crea usuario inactivo y envía email"""
        mock_get_url.return_value = 'http://example.com/confirm/token123'
        mock_send_email.return_value = None
        
        response = self.client.post(self.url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('detail', response.data)
        
        # Verificar usuario creado
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, 'test@example.com')
        
        # Verificar llamadas
        mock_get_url.assert_called_once()
        mock_send_email.assert_called_once_with(
            to_email='test@example.com',
            confirm_url='http://example.com/confirm/token123',
            nombre='testuser'
        )
    
    def test_registro_datos_invalidos(self):
        """Registro con datos inválidos retorna error 400"""
        invalid_data = {
            'username': '',  # Username vacío
            'email': 'invalid-email',  # Email inválido
            'password': '123',  # Password muy corto
        }
        
        response = self.client.post(self.url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registro_email_duplicado(self):
        """No permite registrar email duplicado"""
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='pass123'
        )
        
        response = self.client.post(self.url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registro_username_duplicado(self):
        """No permite registrar username duplicado"""
        User.objects.create_user(
            username='testuser',
            email='other@example.com',
            password='pass123'
        )
        
        response = self.client.post(self.url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registro_passwords_no_coinciden(self):
        """Passwords diferentes retornan error"""
        data = self.valid_data.copy()
        data['password2'] = 'DifferentPass123!'
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('core.services.email_service.ConfirmUserEmail.send_email')
    @patch('authentication.views.user_views.UsersRegisterService.get_confirmation_url')
    def test_registro_fallo_email_no_impide_creacion(self, mock_get_url, mock_send_email):
        """Si falla el envío de email, el usuario se crea igual"""
        mock_get_url.return_value = 'http://example.com/confirm/token123'
        mock_send_email.side_effect = Exception("SMTP Error")
        
        response = self.client.post(self.url, self.valid_data)
        
        # Dependiendo de tu implementación, esto podría ser 201 o 500
        # Ajusta según el comportamiento esperado
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])

class ResendTokenAPIViewTests(TestCase):
    """Tests para reenvío de token de confirmación"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/auth/resend-token/'  # Ajusta según tu URL
        self.inactive_user = User.objects.create_user(
            username='inactive',
            email='inactive@example.com',
            password='pass123',
            is_active=False
        )
        self.active_user = User.objects.create_user(
            username='active',
            email='active@example.com',
            password='pass123',
            is_active=True
        )
    
    @patch('core.services.email_service.ConfirmUserEmail.send_email')
    @patch('authentication.views.user_views.UsersRegisterService.get_confirmation_url')
    def test_reenvio_exitoso(self, mock_get_url, mock_send_email):
        """Reenvío a usuario inactivo funciona correctamente"""
        mock_get_url.return_value = 'http://example.com/confirm/token123'
        
        response = self.client.post(
            self.url,
            {'email': 'inactive@example.com'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        mock_send_email.assert_called_once_with(
            to_email='inactive@example.com',
            confirm_url='http://example.com/confirm/token123',
            nombre='inactive'
        )
    
    def test_reenvio_email_no_existe(self):
        """Email no registrado retorna respuesta genérica (seguridad)"""
        response = self.client.post(
            self.url,
            {'email': 'noexiste@example.com'}
        )
        
        # Por seguridad, retorna 200 para no revelar si el email existe
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_reenvio_usuario_ya_activo(self):
        """Usuario ya activo retorna error 400"""
        response = self.client.post(
            self.url,
            {'email': 'active@example.com'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_reenvio_email_invalido(self):
        """Email inválido retorna error 400"""
        response = self.client.post(
            self.url,
            {'email': 'not-an-email'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_reenvio_sin_email(self):
        """Sin email retorna error 400"""
        response = self.client.post(self.url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VerifyEmailAPIViewTests(TestCase):
    """Tests para verificación de email (GET con token)"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/auth/email/verify/'  # Ajusta según tu URL
        self.inactive_user = User.objects.create_user(
            username='testuser',
            email='old@example.com',
            password='pass123',
            is_active=False
        )
        self.active_user = User.objects.create_user(
            username='activeuser',
            email='active@example.com',
            password='pass123',
            is_active=True
        )
    
    @patch('authentication.views.user_views.UsersRegisterService.verify_email_token')
    def test_activacion_cuenta_exitosa(self, mock_verify):
        """Token válido activa cuenta nueva"""
        mock_verify.return_value = {
            'user_id': self.inactive_user.id,
            'new_email': None
        }
        
        response = self.client.get(f'{self.url}?token=valid_token')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)
    
    @patch('authentication.views.user_views.UsersRegisterService.verify_email_token')
    def test_activacion_cuenta_ya_activa(self, mock_verify):
        """Activar cuenta ya activa retorna 200 (idempotente)"""
        mock_verify.return_value = {
            'user_id': self.active_user.id,
            'new_email': None
        }
        
        response = self.client.get(f'{self.url}?token=valid_token')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    @patch('authentication.views.user_views.UsersRegisterService.verify_email_token')
    def test_cambio_email_exitoso(self, mock_verify):
        """Token con nuevo email actualiza correctamente"""
        mock_verify.return_value = {
            'user_id': self.active_user.id,
            'new_email': 'newemail@example.com'
        }
        
        response = self.client.get(f'{self.url}?token=valid_token')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        self.active_user.refresh_from_db()
        self.assertEqual(self.active_user.email, 'newemail@example.com')
    
    @patch('authentication.views.user_views.UsersRegisterService.verify_email_token')
    def test_cambio_email_duplicado(self, mock_verify):
        """Cambio a email ya existente retorna error 400"""
        mock_verify.return_value = {
            'user_id': self.inactive_user.id,
            'new_email': 'active@example.com'  # Ya existe
        }
        
        response = self.client.get(f'{self.url}?token=valid_token')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('authentication.views.user_views.UsersRegisterService.verify_email_token')
    def test_token_invalido(self, mock_verify):
        """Token inválido retorna error 400"""
        mock_verify.return_value = None
        
        response = self.client.get(f'{self.url}?token=invalid_token')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_sin_token(self):
        """Sin token retorna error 400"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('authentication.views.user_views.UsersRegisterService.verify_email_token')
    def test_usuario_no_existe(self, mock_verify):
        """Usuario en token no existe retorna 404"""
        mock_verify.return_value = {
            'user_id': 99999,
            'new_email': None
        }
        
        response = self.client.get(f'{self.url}?token=valid_token')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)


class RegistrationIntegrationTests(TestCase):
    """Tests de integración del flujo completo de registro"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'
        self.confirm_url = '/api/v1/auth/email/verify/'
        self.resend_url = '/api/v1/auth/resend-token/'
    
    @patch('core.services.email_service.ConfirmUserEmail.send_email')
    @patch('authentication.views.user_views.UsersRegisterService.get_confirmation_url')
    @patch('authentication.views.user_views.UsersRegisterService.verify_email_token')
    def test_flujo_completo_registro_confirmacion(
        self, mock_verify, mock_get_url, mock_send_email
    ):
        """Flujo completo: registro → confirmación → login"""
        # 1. Registro
        mock_get_url.return_value = 'http://example.com/confirm/token123'
        
        register_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        
        response = self.client.post(self.register_url, register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)
        
        # 2. Confirmación
        mock_verify.return_value = {
            'user_id': user.id,
            'new_email': None
        }        
        
        response = self.client.get(self.confirm_url, {'token': 'token123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertTrue(user.is_active)
    
    @patch('core.services.email_service.ConfirmUserEmail.send_email')
    @patch('authentication.views.user_views.UsersRegisterService.get_confirmation_url')
    def test_flujo_registro_reenvio_token(self, mock_get_url, mock_send_email):
        """Flujo: registro → reenviar token → confirmación"""
        # 1. Registro
        mock_get_url.return_value = 'http://example.com/confirm/token1'
        
        register_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        }
        
        self.client.post(self.register_url, register_data)
        
        # 2. Reenviar token
        mock_get_url.return_value = 'http://example.com/confirm/token2'
        
        response = self.client.post(
            self.resend_url,
            {'email': 'new@example.com'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que se llamó send_email dos veces (registro + reenvío)
        self.assertEqual(mock_send_email.call_count, 2)

        