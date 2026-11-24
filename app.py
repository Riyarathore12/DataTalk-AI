from flask import Flask,request,jsonify,send_file,render_template,session
import pandas as pd, io, os, uuid
from engine import overview,ask,clean
app=Flask(__name__); app.secret_key=os.environ.get('SECRET_KEY',os.urandom(32)); app.config['MAX_CONTENT_LENGTH']=15*1024*1024
store={}
def current():
    if session.get('id') not in store: raise ValueError('Upload a dataset first.')
    return store[session['id']]
@app.errorhandler(ValueError)
def err(e): return jsonify(error=str(e)),400
@app.get('/')
def home(): return render_template('index.html')
@app.post('/api/upload')
def upload():
    f=request.files.get('file');
    if not f: raise ValueError('Select a file.')
    try:
        if f.filename.lower().endswith('.csv'): df=pd.read_csv(f)
        elif f.filename.lower().endswith('.xlsx'): df=pd.read_excel(f)
        else: raise ValueError('Use CSV or XLSX.')
    except Exception as e: raise ValueError('Unable to read dataset: '+str(e))
    if df.empty or len(df)>100000 or len(df.columns)>100: raise ValueError('Use 1–100,000 rows and up to 100 columns.')
    key=session.setdefault('id',uuid.uuid4().hex); store[key]=df; return jsonify(overview(df))
@app.post('/api/ask')
def query(): return jsonify(ask(current(),request.json.get('question','')))
@app.post('/api/clean')
def cleaning():
    df=clean(current(),request.json.get('method')); store[session['id']]=df; return jsonify(overview(df))
@app.get('/api/export')
def export(): return send_file(io.BytesIO(current().to_csv(index=False).encode()),mimetype='text/csv',as_attachment=True,download_name='cleaned.csv')
if __name__=='__main__': app.run(host='0.0.0.0',port=8504)
