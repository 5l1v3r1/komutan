# -*- coding: utf-8 -*-
import os,time
import copy
import json
import socket
from flask import Flask,redirect,url_for,session
from flask import g
from flask import render_template #render yapmak icin
from flask import request 
from flask import Response
from arge import *
from random import randint
import codecs
import sqlite3 as sqlmak
import subprocess
from htmlrapor import *
import psutil

ag_bilgi_komut="ifconfig"#"nmcli con show"
arger=Arge()
KULL_ID=-1
SECRET_KEY = 'sds234fv'

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def anaModul():
	if "KULL_ID" in session and arger.girdi_kontrol(session['KULL_ID']) :
			return render_template('anaModul.html')
	return redirect(url_for('giris'))
	
@app.route('/onkar')
def onkar():
	return "python-flask tabanli linux bilgi ve komut yonetim sunucusu- LKomutan"
	#return render_template('anasayfa.html')

@app.route('/cikis')
def cikis():
	arger.girdi_sil(session['KULL_ID'])
	session['KULL_ID']=-1
	return render_template('giris.html')
	
@app.route('/giris', methods=['GET', 'POST'])
def giris():
	error = None
	
	if request.method == 'POST':
		isim=request.form['username']
		sifre=request.form['password']
		#eski bash kontrol
		#sifre_kontkom="komuta/sifre_kontrol.sh "+isim+" "+sifre+" > kondarma/onay"
		#os.system(sifre_kontkom)
		#onayson=open("kondarma/onay","r").read()
		onayson=arger.sifre_kontrol(isim,sifre)
		print "giris onayi:",onayson
		if(onayson):
			print isim,"girisi:"
			arger.girdi_ekle(isim)
			print isim,"onaylandi."
			session['KULL_ID']=isim
			return render_template('anaModul.html')
	return render_template('giris.html', error=error)

@app.route('/giris_eski', methods=['GET', 'POST'])
def giris_eski():
	error = None
	session["KULL_ID"]=-1
	if request.method == 'POST':
		isim=request.form['username']
		sifre=request.form['password']
		id=arger.girdi_no(isim,sifre)
		if(id):
			if arger.girdi_kontrol(id) is None:
				arger.girdi_ekle(id)
			session['KULL_ID']=id
			return render_template('anaModul.html')
	return render_template('giris.html', error=error)

@app.route('/komutaModul', methods=['GET', 'POST'])	
def komutaModul():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		dizin='komuta'
		calismalist=arger.dizin_cek(dizin="komuta")
		return render_template('komutaModul.html',mod=dizin,komutlar=calismalist,kayitmodu='w')	
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	
		
@app.route('/surecModul', methods=['GET', 'POST'])	
def surecModul():
	if "KULL_ID" not in session:
		session['KULL_ID']=-1
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		surecler=arger.komut_kos("netstat -natpl","sh")
		surecler=surecler.split("\n")
		'''rapor="<html><table  border=1  align=left>"
		for surec in surecler:
			if "Active" not in surec and "Proto" not in surec: 
				rapor+="<tr>"
				for sur in surec.split():
					rapor+="<td>"+sur+"</td>"
				rapor+="</tr>"
		rapor+="</table></html>"'''
		rapor=statikrapor()
		dizibas=[]
		top_sutlar=[]
		rapor_html=rapor.diziYhtml2(surecler,dizibas,top_sutlar)
		rapor=rapor_html
		return render_template('surecModul.html')+rapor
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	
		
@app.route('/arayuzModul', methods=['GET', 'POST'])	
def arayuzModul():
	girdimi=arger.girdi_kontrol(session['KULL_ID'])
	if ("KULL_ID" in session and girdimi) :
		dizin='templates'
		arayuzlist=arger.dizin_cek(dizin="templates")
		return render_template('arayuzModul.html',mod=dizin,arayuzler=arayuzlist,kayitmodu='w')	
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")	

@app.route('/komutCalistir', methods=['GET', 'POST'])
def komutCalistir():
	onay=1
	if(onay==1):
		komut=request.form["calismakod"]
		komutson=""
		onkomut=""
		komutdos=request.form["calismalist"]
		if ".sh" in komutdos:
			komut=komut.split("\n")
			for kom in komut:
				komek=kom
				if '=' in kom and 'if ' not in kom:
					baslik=kom.split('=')[0]
					deger=kom.split('=')[1]
					ydeger=request.form[baslik]
					komek=baslik+"="+str(ydeger)
				komutson+=komek+"\n"
			onkomut=""
		else:
			komutson=komut
		if "#python" in komut:
			onkomut="python "
		
		sonuc=arger.komut_kos(komutson,onkomut)
		return Response(json.dumps(sonuc),mimetype='application/json')
	else:		
		return render_template('giris.html', error="isim ve sifre giriniz")

@app.route('/calismaAl', methods=['GET', 'POST'])
def komutAl():
	onay=1
	if(onay==1):
		if('mod' in request.args):
			dizin = request.args.get('mod')
		else:
			dizin='komuta'
		if('dosya' in request.args):
			dosya = request.args.get('dosya')
		else:
			dosya='test.sh'
		data=codecs.open(dizin+"/"+dosya,"r").read()
		return Response(json.dumps(data),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")


@app.route('/calismaKaydet', methods=['GET', 'POST'])
def calismaKaydet():
	onay=1
	if(onay==1):
		kayitmodu = request.form['kayitmodu']
		komut = request.form['calismakod']
		if(kayitmodu=='w'):
			dosya = request.form['yenicalisma']
		else:
			dosya = request.form['calismalist']
		dizin = request.form['mod']
		test=codecs.open(dizin+"/"+dosya,"w","utf-8").write(komut)
		sonuc="tamam"
		return Response(json.dumps(sonuc),mimetype='application/json')
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")
	
@app.route('/agModul')
def agModul():
	
	return render_template('ag.html')
	
@app.route('/arayuzModul_eski', methods=['GET', 'POST'])
def arayuzModul_eski():
	onay=1
	if(onay==1):
		html="<html>"
		komutdos = request.args.get('kd')#"komuta/paket_kur.sh"
		komut=codecs.open("komuta/"+komutdos,"r",'utf-8').read()
		komut=komut.split("\n")
		html+=komutdos+"<p>"
		for kom in komut:
			if '=' in kom and 'if' not in kom:
				deger=kom.split('=')[1]
				deguz=len(kom.split('=')[1])*8+10
				html+=kom.split('=')[0]+":"+"<input type=text id="+kom.split('=')[0]+" name="+kom.split('=')[0]+"  value="+deger+" tabindex='-1' style='width:"+str(deguz)+"px;'/>"+"<br>"
		html+="<p>"+"<input type='submit' name='calistir' id='calistir' value='betik_kos' tabindex='-1'/>"+"<p>"
		html+="<a href='/'><img src='/static/ana.png' class='hover' hinttext='anasayfa' style='margin-right:120px;'></a>" 
		html+="<a href='/komutaModul'><img src='/static/komuta.png' class='hover' hinttext='komuta' style='margin-right:120px;'></a>" 
		html+=""+"</html>"
		return html
	else:
		return render_template('giris.html', error="isim ve sifre giriniz")

@app.route('/ag_bilgi', methods=['GET', 'POST'])
def ag_bilgi():
	onay=1
	if(onay==1):
		#rapor="AG BILGILERI<br>"
		fname="agModul.kom"
		komutsan=""
		rapor="<html>"
		with open(fname) as f:
			ag_komutdos = f.readlines()
		for komutdos in ag_komutdos:
			komutson="<strong>"+komutdos.strip()+"</strong><br>"+arger.komut_doskos(komutdos.strip())
			rapor+=komutson+"<br>"
		rapor+="</html>"
		return Response(json.dumps(rapor),mimetype='application/json')
	return render_template('giris.html', error="isim ve sifre giriniz")

if __name__ == '__main__':
	host="0.0.0.0"
	port_calis=6060
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		sock.connect_ex((host,port_calis))
		app.run(host=host,port=port_calis,debug=True,use_evalex=False,threaded=True) 
	except Exception, e:
		if "Errno 98" in str(e):
			print "Komutan zaten çalışıyor.Port kullanımda."
		
