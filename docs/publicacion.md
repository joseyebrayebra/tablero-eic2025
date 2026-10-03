# Publicación del tablero para un grupo reducido

Servicio: Streamlit Community Cloud, con acceso restringido a correos invitados. Se publica solo lo que el
tablero necesita (`app/`, `config/`, `data/output/`, unos 3.5 MB); los microdatos no salen del equipo.

## Una sola vez

1. **Cuentas.** Crea una cuenta en github.com y entra a share.streamlit.io con esa cuenta de GitHub.
2. **Subir el proyecto a GitHub como repositorio privado.** La forma más sencilla es GitHub Desktop:
   *File → Add local repository →* elige la carpeta `tablero-eic2025` *→ Publish repository*, con la casilla
   *Keep this code private* marcada.
3. **Crear la app.** En share.streamlit.io: *Create app → Deploy a public app from GitHub* (el nombre es del
   botón; la privacidad se ajusta en el paso 4). Repositorio `tablero-eic2025`, rama `main`, archivo principal
   `app/tablero.py`. En *Advanced settings* elige **Python 3.12** y pulsa *Deploy*.
4. **Restringir el acceso.** En la app publicada: *Settings → Sharing → Only specific people can view this app*
   y agrega los correos de tu oficina. Cada persona entra con ese correo (cuenta de Google o enlace por correo).
5. **Compartir el enlace** (`https://<nombre>.streamlit.app`) con las personas invitadas.

Revisa al publicar las condiciones vigentes del plan gratuito para apps privadas; si el plan no lo permite,
la alternativa es el servidor de tu institución (ver abajo).

## Cada vez que cambien las cifras

1. En tu equipo, regenera las salidas (ver `docs/tablero.md`).
2. En GitHub Desktop: escribe un resumen del cambio, *Commit to main* y *Push origin*.
3. La app publicada se actualiza sola en uno o dos minutos.

Cambiar solo las reglas del semáforo es igual: edita `config/semaforo.yaml`, *Commit* y *Push*.

## Alternativas

- **Servidor de la institución:** el área de TI instala Python 3.12, ejecuta `pip install -r requirements.txt`
  y `streamlit run app/tablero.py --server.port 8501` detrás del servidor web institucional.
- **Demostración rápida en la misma red:** en tu equipo,
  `streamlit run app/tablero.py --server.address 0.0.0.0` y comparte `http://<IP de tu equipo>:8501`.
  Solo funciona mientras tu equipo esté encendido y dentro de la red de la oficina.
