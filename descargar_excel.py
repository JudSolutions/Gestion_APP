from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.user_credential import UserCredential

# 🔹 URL de tu sitio y archivo en SharePoint
#sharepoint_site = "https://grchia.sharepoint.com/sites/SAT-ServiciosAdministrativos"
#ruta_archivo = "/sites/SAT-ServiciosAdministrativos/Documentos compartidos/2_Evaluación y Aseguramiento/LGDO/7_Estandar Operativo de Productividad/Auxiliares/2025/10.Octubre/LGDO-AG2_EOP_octubre2025.xlsm"
archivo_local = "C:\Users\USUARIO\Documents\Gestion_APP\LGDO-AG2_EOP_noviembre2025"

# 🔹 Tus credenciales de Office 365
usuario = ""
contrasena = ""

# 🔹 Conexión al sitio SharePoint
ctx = ClientContext(sharepoint_site).with_credentials(UserCredential(usuario, contrasena))

try:
    response = ctx.web.get_file_by_server_relative_url(ruta_archivo).download(archivo_local).execute_query()
    print(f"✅ Archivo descargado correctamente como: {archivo_local}")
except Exception as e:
    print(f"❌ Error al descargar el archivo: {e}")
