# Blackboard-downloader
Automate download of EV resources (Blackboard)

## ¿Qué es?
Esto es un script específico para automatizar la descarga de todos los recursos de todos los cursos disponibles de ev.us.es (Blackboard).

## Requerimientos
Se necesita de tener principalmente de dos cosas:
### Google Chrome
https://www.google.com/intl/es_es/chrome/?brand=AJCO&ds_kid=328709829484&gclsrc=aw.ds&gad_source=1&gad_campaignid=22911405483&gclid=Cj0KCQiA-YvMBhDtARIsAHZuUzKstexgy48zKHyJBEZTWDUOBuVekczLsBKO4fSfVDYOg66rIe2FHFUaAlrpEALw_wcB 

Google Chrome instalado OBLIGATORIAMENTE, PREFERIBLEMENTE con sesión iniciada.

### Authenticator Extension
https://chromewebstore.google.com/detail/authenticator/bhghoamapcdpbohphigoooaddinpkbai?hl=en-US&utm_source=ext_sidebar

Extensión `Authenticator` OBLIGATORIAMENTE
1. La extensión se descarga en Chrome
2. 2. Se añade el código en la extensión (seguir documentación de añadir dispositivo para 2FA) -> Ejemplo: https://sic.us.es/servicios/cuentas-y-accesos-los-servicios/gestion-de-usuarios-y-contrasenas-uvus/doble-factor-de-autenticacion

## Configuración previa
Es necesario descargar el archivo de `copia de seguridad` de la extensión para obtener el token de seguridad:
1. Authenticator > Ajustes > Copia de seguridad > Descargar una copia de seguridad

## Utilización
1. Ejecutar archivo `.exe`
2. Introducir credenciales: UVUS y Contraseña -> OJO: la contraseña no se ve
3. Seleccionar archivo descargado de Authenticator
4. Elegir ruta de descarga
