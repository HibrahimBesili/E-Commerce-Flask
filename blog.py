from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmanız gerekmektedir","danger")
            return redirect(url_for("login"))
    return decorated_function




#Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username=StringField("Kullanıcı Adı",validators=[validators.length(min=5,max=35)])
    email=StringField("Email:",validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz")])
    password=PasswordField("Parola:",validators=[validators.DataRequired("Lütfen bir parola belirleyiniz"),
    validators.EqualTo(fieldname="confirm",message="Parolanız yanlış")
    ])
    confirm=PasswordField("Parola Doğrula")

class LoginForm(Form):
    username=StringField("Kullanıcı Adı:")
    password=PasswordField("Parola")

app= Flask(__name__)
app.secret_key= "ybblog"

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ybblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)




@app.route("/")
def index():
    return render_template("index.html")
@app.route("/article/<string:id>")
def detail(id):
    return "Article Id"+ id

@app.route("/about")
def about():
    return render_template("about.html")

#login işlemi
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
       username = form.username.data
       password_entered = form.password.data

       cursor = mysql.connection.cursor()

       sorgu = "Select * From users where username = %s"

       result = cursor.execute(sorgu,(username,))

       if result > 0:
           data = cursor.fetchone()
           real_password = data["password"]
           if sha256_crypt.verify(password_entered,real_password):
               flash("Başarıyla Giriş Yaptınız...","success")

               session["logged_in"]=True
               session["username"]= username


               return redirect(url_for("index"))
           else:
               flash("Parolanızı Yanlış Girdiniz...","danger")
               return redirect(url_for("login")) 

       else:
           flash("Böyle bir kullanıcı bulunmuyor...","danger")
           return redirect(url_for("login"))

    
    return render_template("login.html",form = form)




#Kontrol paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="select * from product where username=%s"

    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        products=cursor.fetchall()
        return render_template("dashboard.html",products=products)
    else:
        return render_template("dashboard.html")

#Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


#Kayıt Olma
@app.route("/register",methods=["GET","POST"])
def register():
    form =RegisterForm(request.form)

    if request.method=="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        cursor=mysql.connection.cursor()

        sorgu="Insert into users(name,email,username,password)VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))

        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)
#ürünleri gösterme
@app.route("/products")
def products():
    cursor=mysql.connection.cursor()
    
    sorgu="Select * from product"

    result = cursor.execute(sorgu)

    if result>0:
        products=cursor.fetchall()
        return render_template("products.html",products=products)
    else:
        return render_template("products.html")



#Detay Sayfası
@app.route("/products/<string:pid>")
def product(pid):
    cursor=mysql.connection.cursor()

    sorgu="Select * from product where pid=%s"

    result=cursor.execute(sorgu,(pid,))
    if result>0:
        product=cursor.fetchone()
        return render_template("product.html",product=product)

    else:
        return render_template("product.html")

#ürün ekleme
@app.route("/addproduct",methods =["GET","POST"])
def addproduct():
    form=ProductForm(request.form)
    if request.method == "POST":
        ptype=form.ptype.data
        pname=form.pname.data
        pcost=form.pcost.data

        cursor=mysql.connection.cursor()
        sorgu="Insert into product(username,type,pname,pcost) VALUES (%s,%s,%s,%s)" 

        cursor.execute(sorgu,(session["username"],ptype,pname,pcost)) 
        
        mysql.connection.commit()

        cursor.close()

        flash("Ürün ekleme işleminiz başarıyla gerçekleşmiştir","success")
        return redirect(url_for("dashboard"))
    
   
    return render_template("addproduct.html",form=form)
#Ürün silme
@app.route("/delete/<string:pid>")
@login_required
def delete(pid):
    sorgu="select * from product where username=%s and pid=%s"
    cursor=mysql.connection.cursor()
    result=cursor.execute(sorgu,(session["username"],pid))
    if result>0:
        sorgu2="Delete from product where pid=%s"
        cursor.execute(sorgu2,(pid,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir ürün yok veya bu işleme yetkiniz yoktur")
        return redirect(url_for("index"))
#Sepete Ekleme
@app.route("/addtobasket<string:pid>"")
@login_required
def addtobasket():
    form=ProductForm(request.form)
    pptype=form.ptype.data
    ppname=form.pname.data
    ppcost=form.pcost.data
    sorgu="Insert into users(ptype,pname,pcost)VALUES(%s,%s,%s)"
    cursor=mysql.connection.cursor()
    cursor.execute(sorgu2,(pptype,ppname,ppcost,pid))
    mysql.connection.commit()
    cursor.close()
    
  

#Ürün güncelleme
@app.route("/edit/<string:pid>",methods=["GET","POST"])
@login_required
def update(pid):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="select * from product where username=%s and pid=%s"
        result=cursor.execute(sorgu,(session["username"],pid))
        if result==0:
            flash("Böyle bir makale yok veya buna yetkiniz yok")
            return redirect(url_for("index"))
        else:
            product=cursor.fetchone()
            form=ProductForm()
            
            form.ptype.data=product["type"]
            form.pname.data=product["pname"]
            form.pcost.data=product["pcost"]
            return render_template("update.html",form=form)
            
    else:
        #Post Request
        form=ProductForm(request.form)
        pptype=form.ptype.data
        ppname=form.pname.data
        ppcost=form.pcost.data

        sorgu2="Update product Set type=%s,pname=%s,pcost=%s where pid=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(pptype,ppname,ppcost,pid))
        mysql.connection.commit()

        flash("Ürün başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))

#Ürün Arama
@app.route("/search",methods =["GET","POST"])
def search():
    if request.method =="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()

        sorgu="Select * from product where pname like '%"+keyword+"%'" 

        result=cursor.execute(sorgu)
        if result ==0:
            flash("Aranan ürün bulunamadı")
            return redirect(url_for("products"))
        else:
            products=cursor.fetchall()

            return render_template("products.html",products=products)



#Ürün Form

class ProductForm(Form):
    ptype=StringField("Ürün Türü")
    pname=StringField("Ürün Adı")
    pcost=StringField("Ürün Değeri")
    

if __name__ == '__main__':
    app.run(debug=True)
