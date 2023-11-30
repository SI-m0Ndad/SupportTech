from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solicitudes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Ruta para la carpeta de archivos subidos
db = SQLAlchemy(app)

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = '20300083@uttt.edu.mx'  # Reemplaza con tu dirección de correo
EMAIL_PASSWORD = 'FSS2383F'  # Reemplaza con tu contraseña de correo


class Solicitud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(100))
    area = db.Column(db.String(50))
    urgencia = db.Column(db.String(50))
    fecha_inicio = db.Column(db.Date)
    descripcion = db.Column(db.Text)
    evidencia = db.Column(db.String(100))  # Nombre del archivo de evidencia

# Ruta para el formulario
@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        # Procesar los datos del formulario
        nombre = request.form['nombre']
        email = request.form['email']
        area = request.form['area']
        urgencia = request.form['urgencia']
        fecha_inicio_str = request.form['fecha_inicio']  # Obtener la fecha como cadena
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()  # Convertir la cadena a objeto de fecha
        descripcion = request.form['descripcion']
        evidencia = request.files['evidencia']

        # Guardar la solicitud en la base de datos
        nueva_solicitud = Solicitud(
            nombre=nombre,
            email=email,
            area=area,
            urgencia=urgencia,
            fecha_inicio=fecha_inicio,
            descripcion=descripcion,
            evidencia=evidencia.filename if evidencia else None
        )

        db.session.add(nueva_solicitud)
        db.session.commit()

        # Guardar el archivo de evidencia si se proporcionó
        if evidencia:
            evidencia.save(os.path.join(app.config['UPLOAD_FOLDER'], evidencia.filename))

        # Envío de correo de confirmación
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = 'Confirmación de envío'

        body = f'¡Gracias por enviar el formulario, {nombre}!'
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Error al enviar el correo: {e}")

        return redirect(url_for('confirmacion'))  # Redireccionar a la página de éxito

    return render_template('form.html')

# Ruta para la página de éxito (confirmación)
@app.route('/confirmacion')
def confirmacion():
    return render_template('success.html')

# Ruta para la vista de administración (solo accesible para administradores)
@app.route('/admin')
def administracion():
    # Consultar todas las solicitudes de la base de datos
    solicitudes = Solicitud.query.all()
    return render_template('admin.html', solicitudes=solicitudes)

@app.route('/view_evidence/<filename>', methods=['GET'])
def view_evidence(filename):
    # Ruta completa del archivo de evidencia
    evidencia_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Comprobar si el archivo existe en la carpeta de uploads
    if os.path.isfile(evidencia_path):
        # Si el archivo existe, muestra el archivo en línea
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        # Si el archivo no existe, devuelve un mensaje de error o redirige a una página de error
        return "Archivo no encontrado", 404

@app.route('/download_evidence/<filename>', methods=['GET'])
def download_evidence(filename):
    # Ruta completa del archivo de evidencia
    evidencia_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Comprobar si el archivo existe en la carpeta de uploads
    if os.path.isfile(evidencia_path):
        # Si el archivo existe, descarga el archivo
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    else:
        # Si el archivo no existe, devuelve un mensaje de error o redirige a una página de error
        return "Archivo no encontrado", 404

if __name__ == '__main__':
    # Crear la carpeta de subida de archivos si no existe
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    with app.app_context():
        db.create_all()

    app.run(debug=True)
