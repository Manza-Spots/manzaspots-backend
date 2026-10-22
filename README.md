# manzaspots-backend
## Correo

`EMAIL_PROVIDER` en el `.env` elige cómo se envían los correos de la cuenta (verificar correo,
restablecer contraseña, cambio de correo):

| Valor | Para | Variables |
|---|---|---|
| `resend` (por defecto) | Despliegue | `RESEND_API_KEY`. El remitente (`no-reply@DOMAIN`) debe ser de un dominio verificado en Resend; si no, Resend rechaza el envío (550). |
| `gmail` | Desarrollo local | `EMAIL_HOST_USER` (la cuenta de Gmail) y `EMAIL_HOST_PASSWORD` (contraseña de aplicación). El remitente es esa cuenta. |
| `console` | Pruebas sin enviar | Ninguna: el correo se imprime en el log. |

`DEFAULT_FROM_EMAIL` permite fijar otro remitente, por ejemplo `Manza Spots <hola@manzaspots.app>`.
