class UserMessages:
    """Mensajes centralizados para usuarios"""
    
    # Success messages
    USER_CREATED = "Usuario creado. Revisa tu correo para verificar la cuenta."
    USER_VERIFIED = "Usuario verificado con éxito."
    USER_ACTIVATED = "Usuario {username} activado."
    USER_DEACTIVATED = "Usuario {username} desactivado."
    VERIFICATION_EMAIL_SENT = "Correo de verificación enviado"
    EMAIL_ALREADY_VERIFIED = "La cuenta ya fue verificada"
    
    # Error messages
    TOKEN_NOT_PROVIDED = "Token no proporcionado."
    TOKEN_INVALID = "Token inválido o expirado."
    USER_NOT_FOUND = "Usuario no encontrado."
    USER_ALREADY_VERIFIED = "El usuario ya fue verificado."
    EMAIL_REQUIRED = "Email is required"
    EMAIL_NOT_AVAIBLE = "El email ya está en uso"
    NEW_EMAIL = "Email actuializo exitosamente"
    # Info messages
    EMAIL_SENT_IF_EXISTS = "Si el correo existe, te llegará una notificación a tu correo con instrucciones."
    LOGIN = "Inicio de Sesion exitoso"

class AuthMessages:
    # Success messages
    CONFIRM_NEW_PASSWORD = "Contraseña restablecida con éxito."
    
    # Error messages
    PASSWORDL_REQUIRED = 'el campo password es requerido'
    EMAIL_USERNAMEL_REQUIRED = 'Debe proporcionar username o email'
    CREDENTIALS_INVALID = 'Credenciales inválidas'


class ErrorMessages:
    """
    Mensajes de respuesta de API para errores manejados por SentryErrorHandlerMixin
    """
    
    # Errores de OAuth
    OAUTH_ERROR = "Error en autenticación con proveedor externo. Intenta nuevamente, verifica el token"
    
    # Errores de validación Django
    INVALID_DATA = "Datos inválidos"
    
    # Errores de integridad (Database)
    RESOURCE_EXISTS = "El recurso ya existe"
    INVALID_REFERENCE = "Referencia inválida"
    DATA_INTEGRITY_ERROR = "Error de integridad de datos"
    
    # Errores críticos de base de datos
    DATABASE_ERROR = "Error del sistema. Por favor intenta más tarde."
    
    # Errores de email
    EMAIL_NOTIFICATION_PENDING = "Operación completada (notificación pendiente)"
    
    # Errores de APIs externas
    SERVICE_TIMEOUT = "El servicio tardó demasiado. Por favor intenta nuevamente."
    SERVICE_UNAVAILABLE = "Servicio no disponible. Por favor intenta más tarde."
    EXTERNAL_API_ERROR = "Error comunicándose con servicio externo."
    
    # Errores inesperados/generales
    UNEXPECTED_ERROR = "Error inesperado. Revisa los logs"
    
    # Mensajes de éxito por defecto
    DEFAULT_SUCCESS = "Operación exitosa"
    
    # Errores de conexión
    CONNECTION_ERROR = "Error de conexión"
    
    # Mensajes específicos por tipo de operación
    class Authentication:
        OAUTH_FAILED = "No se pudo autenticar con el proveedor externo"
        TOKEN_EXPIRED = "Token de acceso expirado o inválido"
    
    class Database:
        DUPLICATE_ENTRY = "Ya existe un registro con estos datos"
        FOREIGN_KEY_VIOLATION = "Referencia a recurso inexistente"
        CONSTRAINT_VIOLATION = "Violación de restricción de datos"
    
    class Network:
        CONNECTION_LOST = "Conexión perdida con el servidor"
        SSL_ERROR = "Error de certificado SSL"
        DNS_ERROR = "No se puede resolver el nombre del servidor"
    
    class FileSystem:
        UPLOAD_FAILED = "Error al subir el archivo"
        FILE_TOO_LARGE = "El archivo excede el tamaño permitido"
        INVALID_FILE_TYPE = "Tipo de archivo no permitido"