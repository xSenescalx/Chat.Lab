# Ngrok ----- ver q onda es esto (para convertir localhost en servidor de acceso abierto?)
# Login: https://www.youtube.com/watch?v=2Zz97NVbH0U&t=31s
# SQL: https://www.youtube.com/watch?v=51F_frStZCQ
# MySQL database: https://www.freemysqlhosting.net/
# Dark Mode: https://www.youtube.com/watch?v=WsoL4MIhJbg
# Mail verification: https://www.youtube.com/watch?v=ByoCkmilHg0

from threading import active_count
import pusher
import os
import uuid
from flask import (
    Flask,
    jsonify,                   # g: Se usa para pasar la info del usuario que este conectado. Tamb se puede evitar que cualquiera entre a un template privado.
    redirect,
    render_template,
    request,
    session,             # session: guarda un int en una variable global.
    url_for
)
from flask_mysqldb import MySQL
from flask_mail import Connection, Mail, Message
from flask_session import Session
from tempfile import mkdtemp
from random import *
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required




# Nombre de la app
app = Flask(__name__)
app.config['DEBUG'] = True

if __name__ == '__main__':
    app.run()


# Pusher

pusher_client = pusher.Pusher(
  app_id='1237593',
  key='eae3df9de1df6d4b8c82',
  secret='668684af6ae5bad88300',
  cluster='us2',
  ssl=True
)



# Para mandar mails!

mail = Mail(app)

app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = 'pruebasflask@gmail.com'
app.config["MAIL_PASSWORD"] = 'wersdfxcv'
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)

# Contraseña random que se enviara al mail.
otp = randint(000000,999999)

# secret key es necesario para trabajar con sesiones, la contraseña puede ser cualquiera
app.secret_key = 'danidani'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configuracion basica para poder usar la base de datos, la info te la mandan por mail desde esta pag: https://www.freemysqlhosting.net/


app.config['MYSEQL_USER'] = 'dani'
app.config['MYSEQL_PASSWORD'] = '3a9761pa'
app.config['MYSEQL_HOST'] = 'localhost'
app.config['MYSQL_DB'] = 'chatapp'

mysql = MySQL(app)   
        

@app.route('/')
def index():
    return render_template('/index.html')

@app.route('/info', methods=['GET', 'POST'])
def info():
    if request.method == "POST":
        

        sender_name = request.form['name']
        sender_email = request.form['email']
        sender_proyect = request.form['proyect']
        sender_message = request.form['message']
        my_email = 'daniroffo125@gmail.com'
        

        msg = Message(subject = sender_name + ' ' + sender_email + ':' + ' ' + sender_proyect, sender = sender_email, recipients= my_email.split() )
        msg.body = str(sender_message)
        mail.send(msg)  

        return render_template('/info.html')

    else:

        return render_template('/info.html')

@app.route('/myChat', methods=['GET', 'POST'])
@login_required
def myChat():

    contact_clicked = request.form.get('contact_clicked')
    active_account = session["user_account"]

    cur = mysql.connection.cursor()
    contact_info = ()
    cur.execute("SELECT contacts FROM users_contacts WHERE account = (%s)", [session["user_account"]])
    contacts = cur.fetchall() 
    mysql.connection.commit()
    for contact in contacts:
        
        cur.execute("SELECT username, image, account FROM users WHERE account = (%s)", [contact[0]])
        contact_info = contact_info + cur.fetchall()
        mysql.connection.commit()
    
    cant_contacts = len(contact_info)
    e = 0
    contact_info_lista = []

    for cant_contacts in contact_info:
        
        contact_info_lista.append(contact_info[e][0])
        e = e + 1
    
    
    #para cargar los mensajes viejos en la pantalla

    cur.execute("SELECT conversation_id FROM users_contacts WHERE account = (%s) AND contacts = (%s)", [session["user_account"], contact_clicked])
    
    conversation_id = [item[0] for item in cur.fetchall()]
    mysql.connection.commit()
    conversation_id = "".join([str(_) for _ in conversation_id])
    
    
    if (len(conversation_id) != 0):
        cur.execute("SELECT message, account, time FROM users_messages WHERE conversation_id = (%s)", [conversation_id])
        messages = [items[0] for items in cur.fetchall()]
        cur.execute("SELECT message, account, time FROM users_messages WHERE conversation_id = (%s)", [conversation_id])
        account = [items[1] for items in cur.fetchall()]
        cur.execute("SELECT message, account, time FROM users_messages WHERE conversation_id = (%s)", [conversation_id])
        time = [items[2] for items in cur.fetchall()]
        mysql.connection.commit()
      
        pusher_client.trigger('chat-channel-' + conversation_id , 'old_messages', {'messages': messages, 'account': account, 'time':time, 'lenMsg': len(messages)})
         
    else:
        messages = ""

    cur.execute("SELECT * FROM users_contacts WHERE account = (%s)", [session["user_account"]])
    usercontacts = cur.fetchall()
    mysql.connection.commit()

    cur.execute("SELECT * FROM users_messages WHERE id IN (SELECT MAX(id) FROM users_messages GROUP BY conversation_id) ORDER BY id DESC")
    messages_data = cur.fetchall()
    mysql.connection.commit()
    
    return render_template('/myChat.html', messages_data = messages_data, usercontacts = usercontacts, conversation_id = conversation_id, contact_info = contact_info, cant_contacts = cant_contacts, contact_info_lista = contact_info_lista, active_account = active_account)

@app.route('/chat_message', methods=['GET','POST'])
@login_required
def chat_message():
    
    try:
        
        contact_clicked = request.form.get('contact_clicked')
        message = request.form.get('message')
        time = request.form.get('time')
        active_account = request.form.get('account')

        # falta hacer, recibir mensajes y guardarlos donde corresponde
        cur = mysql.connection.cursor()
        cur.execute("SELECT conversation_id FROM users_contacts WHERE account = (%s) AND contacts = (%s)", [session["user_account"], contact_clicked])        
        conversation_id = [item[0] for item in cur.fetchall()]
        mysql.connection.commit()
        conversation_id = "".join([str(_) for _ in conversation_id])
        
        pusher_client.trigger('chat-channel-' + conversation_id , 'message', {'active_account' : active_account, 'message': message , 'time' : time, 'conversation_id' : conversation_id})
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users_messages (conversation_id, account, message, time) VALUES (%s, %s, %s, %s)", [conversation_id ,session["user_account"], message, time])
        mysql.connection.commit()
        

        

        return jsonify({'result' : 'success'})

    except:

        return jsonify({'result' : 'failure'})



@app.route('/addContact', methods=['GET', 'POST'])
@login_required
def addContact():

    if request.method == "POST":
        contact = request.form["account"]
        random_number = request.form["contactId"]


        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM users WHERE random_number = (%s) AND account = (%s)", [random_number, contact])
        data = cur.fetchall()
        mysql.connection.commit()

        if len(data) != 1 or contact != data[0][1]:
            msgAddContactError = "Wrong Contact or Contact ID, Try Again!"
            return render_template('addContactError.html', msgAddContactError = msgAddContactError)

        #crea un espacio para guardar el contacto del usuario

        cur.execute("SELECT * FROM users_contacts WHERE account = (%s) AND contacts = (%s)", [session["user_account"], contact])
        data = cur.fetchall()
        mysql.connection.commit()

        # Buscar cuantos conversation_id existen

        cur.execute("SELECT conversation_id FROM users_contacts WHERE account = (%s) OR contacts = (%s)", [session["user_account"], contact])
        cant_conversation_id = cur.fetchall()
        mysql.connection.commit()

        cant_conversation_id = len(cant_conversation_id) / 2

        if len(data) == 0:
            
            cant_conversation_id = cant_conversation_id + 1
            cur.execute("INSERT INTO users_contacts (account, contacts, conversation_id) VALUES (%s, %s, %s)", [session["user_account"], contact, cant_conversation_id])
            mysql.connection.commit()
            
        #crea un espacio para guardar los mensajes que le van a llegar al contacto, si es q no existe

        cur.execute("SELECT * FROM users_contacts WHERE account = (%s) AND contacts = (%s)", [contact, session["user_account"]])
        data = cur.fetchall()
        mysql.connection.commit()

        if len(data) == 0:
            
            
            cur.execute("INSERT INTO users_contacts (account, contacts, conversation_id) VALUES (%s, %s, %s)", [contact, session["user_account"], cant_conversation_id])
            mysql.connection.commit()
            

        return render_template('/myChat.html')

    else:

        return render_template('/addContact.html')



@app.route('/addContactError', methods=['GET', 'POST'])
@login_required
def addContactError():

    if request.method == "POST":
        return redirect('addContact')

    else:
        return render_template('/addContactError.html')

    

@app.route('/globalChat')
@login_required
def globalChat():

            
    return render_template('/globalChat.html')
    
    

@app.route('/global_message', methods=['POST'])
@login_required
def global_message():

    try:

        username = request.form.get('username')
        message = request.form.get('message')

        pusher_client.trigger('globalChat-channel', 'new-message', {'username' : username, 'message': message})

        return jsonify({'result' : 'success'})

    except:

        return jsonify({'result' : 'failure'})


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    
    
    if request.method == "POST":
        username = request.form["username"]
        id = session["user_id"]
        profilePic = request.files["profilePic"]
        cur = mysql.connection.cursor()
        
            
        cur.execute("UPDATE users SET username = (%s) WHERE id = (%s)", [username, id])

        mysql.connection.commit()
        cur.execute("SELECT * FROM users WHERE id = (%s)", [id])
        data = cur.fetchall() 

        session["user_name"] = data[0][2]


        if profilePic.filename != "":
            picName = str(uuid.uuid1()) + os.path.splitext(profilePic.filename)[1]
            profilePic.save(os.path.join("static/profile_pics", picName))

            cur.execute("UPDATE users SET image = (%s) WHERE id = (%s)", [picName, id])
            mysql.connection.commit()

            cur.execute("SELECT * FROM users WHERE id = (%s)", [id])
            data = cur.fetchall() 
            mysql.connection.commit()
            session["user_image"] = data[0][5]

            
        image_file = url_for('static', filename='profile_pics/' + session['user_image'])
        

        mysql.connection.commit()

        

        return render_template('/account.html', image_file = image_file)

    else:
        image_file = url_for('static', filename='profile_pics/' + session['user_image'])

        return render_template('/account.html', image_file = image_file)



@app.route('/notifications')
@login_required
def notifications():

    return render_template('/notifications.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        
        cur = mysql.connection.cursor()
        name = request.form['account']
        password = request.form['password']

         # Query database for username
        cur.execute("SELECT * FROM users WHERE account = (%s)", [name])
        data = cur.fetchall()
        mysql.connection.commit()

        # Ensure username exists and password is correct
        if len(data) != 1 or not check_password_hash(data[0][4], (password)):
            msgLoginError = "Wrong Username or Password, Try Again!"
            return render_template('loginError.html', msgLoginError = msgLoginError)
            
        # Remember which user has logged in
        session["user_id"] = data[0][0]
        session["user_account"] = data[0][1]
        session["user_name"] = data[0][2]
        session["user_password"] = data[0][4]
        session["user_email"] = data[0][3]
        session["user_image"] = data[0][5]
        session["user_random_number"] = data[0][6]

        return render_template('/index.html')

    else:

        return render_template('/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    
    if request.method == "POST":
        
        cur = mysql.connection.cursor()
        email = request.form['email']
        name = request.form['account']
        password = request.form['password']



        if request.form["password"] != request.form["confirmation"]:
            msgRegistrationError = "Wrong Confirmation, Try Again!"
            return render_template('registrationError.html', msgRegistrationError = msgRegistrationError)



        cur.execute("SELECT email FROM users WHERE email = (%s)", [email])
        rows = cur.fetchall()
        # Ensure email doesnt exist
        if len(rows) != 0:
            msgRegistrationError = "Email Already Used, Try Again!"
            return render_template('registrationError.html', msgRegistrationError = msgRegistrationError) 

        # Query database for username

        cur.execute("SELECT account FROM users WHERE account = (%s)", [name])
        rows = cur.fetchall()
        
        # Ensure username doesnt exist
        if len(rows) != 0:
            msgRegistrationError = "Account Already Exist, Try Again!"
            return render_template('registrationError.html', msgRegistrationError = msgRegistrationError)


        # Toma los datos del nuevo usuario y manda un email al usuario.
        msg = Message(subject = 'App Security Code', sender = 'pruebasflask@gmail.com', recipients =[email])
        msg.body = str(otp)
        mail.send(msg)   
        cur.execute("DELETE FROM preregister")
        
        
        cur.execute("INSERT INTO preregister (email, account, username, password) VALUES (%s, %s, %s, %s)", (email, name, name, password))
        
        mysql.connection.commit()
        
        return render_template('/registerConfirmation.html')
    else:
        return render_template('/register.html')

@app.route('/registerConfirmation', methods=['GET', 'POST'])
def registerConfirmation():
    # Revisa que el otp enviado al mail sea el mismo q ingresa el usuario, de no serlo lo manda a orpError.html.
    if request.method == "POST":
        user_otp =request.form['otp']
        if otp == int(user_otp):

            #Crear un numero aleatorio de 8 digitos.

            lista = []
            for x in range(8):
                a = randint(0,9)
                lista.append(str(a))
            random_number = ''
            for x in range(8):
                random_number = random_number + lista[x]


            default_image_file = 'default.jpg'

            cur = mysql.connection.cursor()

            
            cur.execute("SELECT * FROM preRegister")
            #fetchall() sirve para recolectar los datos obtenidos con SELECT, si no devuelve un "1" y no los datos de la base de datos
            data = cur.fetchall()

            hash = generate_password_hash(data [0][3])

            

            cur.execute("INSERT INTO users (email, account, username, password, image, random_number) VALUES (%s, %s, %s, %s, %s, %s)", (data[0][2], data[0][0], data[0][1], hash, default_image_file, random_number))

           
            cur.execute("DELETE FROM preRegister")
            mysql.connection.commit()
            return render_template('/registerDone.html')
        else:
            msgError = "Wrong Security Code, Try Again!"
            print(msgError)
            return render_template('otpError.html',msgError = msgError)

    else:
        return render_template('/registerConfirmation.html')

@app.route('/registerDone', methods=['GET', 'POST'])
def registerDone():
    if request.method == "POST":
        return redirect('myChat')
    else:
        
        return render_template('/registerDone.html')

@app.route('/registrationError', methods=['GET', 'POST'])
def registrationError():
    if request.method == "POST":
        return redirect('register')
    else:
        return render_template('/registrationError.html')

@app.route('/loginError', methods=['GET', 'POST'])
def loginError():
    if request.method == "POST":
        return redirect('login')
    else:
        return render_template('/loginError.html')

@app.route('/otpError', methods=['GET', 'POST'])
def otpError():
    if request.method == "POST":
        return redirect('registerConfirmation')
    else:
        return render_template('/otpError.html')

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route('/changePassword', methods=['GET', 'POST'])
@login_required
def changePassword():
    
    if request.method == "POST":
        
        cur = mysql.connection.cursor()
        password = request.form['password']

        if request.form["password"] != request.form["confirmation"]:
            msgPasswordError = "Wrong Confirmation, Try Again!"
            return render_template('changePassError.html', msgPasswordError = msgPasswordError)
        print(session.get("user_email"))

        # Toma los datos del nuevo usuario y manda un email al usuario.
        msg = Message(subject = 'App Security Code', sender = 'pruebasflask@gmail.com', recipients = [session.get("user_email")])
        msg.body = str(otp)
        mail.send(msg)   
        cur.execute("DELETE FROM preregister")
        
        
        cur.execute("INSERT INTO preregister (password) VALUES (%s)", [password])
        
        mysql.connection.commit()

        
        return render_template('/changePassConf.html')
    
    
    else:
    
        return render_template('/changePassword.html')

@app.route('/changePassConf', methods=['GET', 'POST'])
@login_required
def changePassConf():
    # Revisa que el otp enviado al mail sea el mismo q ingresa el usuario, de no serlo lo manda a orpError.html.
    if request.method == "POST":
        user_otp =request.form['otp']
        if otp == int(user_otp):

            cur = mysql.connection.cursor()
            id = session["user_id"]

            cur.execute("SELECT * FROM preRegister")
            #fetchall() sirve para recolectar los datos obtenidos con SELECT, si no devuelve un "1" y no los datos de la base de datos
            data = cur.fetchall()

            hash = generate_password_hash(data [0][3])

            cur.execute("UPDATE users SET password = (%s) WHERE id = (%s)", [hash, id])

            mysql.connection.commit()
            cur.execute("SELECT * FROM users WHERE id = (%s)", [id])
            data = cur.fetchall() 

            session["user_password"] = data[0][3]

           
            cur.execute("DELETE FROM preRegister")
            mysql.connection.commit()


            return render_template('/changePassDone.html')
        else:
            msgError = "Wrong Security Code, Try Again!"
            print(msgError)

            

            return render_template('changeOtpError.html',msgError = msgError)

    else:
        return render_template('/changePassConf.html')

@app.route('/changePassDone', methods=['GET', 'POST'])
@login_required
def changePassDone():
    if request.method == "POST":


        return render_template('/myChat.html')
    else:
        
        return render_template('/changePassDone.html')

@app.route('/changeOtpError', methods=['GET', 'POST'])
@login_required
def changeOtpError():
    if request.method == "POST":

        

        return redirect('changePassConf')
    else:
        return render_template('/changeOtpError.html')



@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():

    if request.method == 'POST':
            
            cur = mysql.connection.cursor()
            name = request.form['account']
            password = request.form['password']
            id = session["user_id"]

            # Query database for username
            cur.execute("SELECT * FROM users WHERE account = (%s)", [name])
            data = cur.fetchall()
            mysql.connection.commit()
            
            # Ensure username match and password is correct
            if name != session["user_account"] or not check_password_hash(data[0][4], (password)):
                msgDeleteError = "Wrong Username or Password, Try Again!"
                return render_template('deleteError.html', msgDeleteError = msgDeleteError)
            
            cur.execute("DELETE FROM users WHERE id = (%s)", [id])
            mysql.connection.commit()
            # Forget any user_id
            session.clear()

            # Redirect user to login form
            return redirect("/")

    else:

            return render_template('/delete.html')

@app.route('/deleteError', methods=['GET', 'POST'])
@login_required
def deleteError():
    if request.method == "POST":
        
        return render_template('/delete.html')
    else:
        return render_template('/deleteError.html')