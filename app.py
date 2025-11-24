from flask import Flask, request, send_file, render_template
import os
import tempfile
from pathlib import Path
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB限制

ALLOWED_EXTENSIONS = {'epub', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_pdf(input_path, output_dir):
    """使用 LibreOffice 转换文件为 PDF"""
    try:
        result = subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_path
        ], check=True, timeout=120, capture_output=True, text=True)
        
        print(f"转换成功: {result.stdout}")
        
        # 找到生成的 PDF 文件
        filename = Path(input_path).stem + '.pdf'
        pdf_path = os.path.join(output_dir, filename)
        
        if os.path.exists(pdf_path):
            return pdf_path
        else:
            print(f"PDF 文件未找到: {pdf_path}")
            return None
            
    except subprocess.TimeoutExpired:
        print("转换超时")
        return None
    except subprocess.CalledProcessError as e:
        print(f"转换失败: {e.stderr}")
        return None
    except Exception as e:
        print(f"错误: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return {'error': '没有上传文件'}, 400
    
    file = request.files['file']
    
    if file.filename == '':
        return {'error': '文件名为空'}, 400
    
    if not allowed_file(file.filename):
        return {'error': '不支持的文件格式'}, 400
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 保存上传的文件
            filename = secure_filename(file.filename)
            input_path = os.path.join(tmpdir, filename)
            file.save(input_path)
            
            print(f"文件已保存: {input_path}")
            
            # 转换为 PDF
            pdf_path = convert_to_pdf(input_path, tmpdir)
            
            if pdf_path and os.path.exists(pdf_path):
                output_filename = Path(filename).stem + '.pdf'
                return send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=output_filename,
                    mimetype='application/pdf'
                )
            else:
                return {'error': '转换失败，请检查文件格式'}, 500
                
    except Exception as e:
        print(f"处理错误: {str(e)}")
        return {'error': f'服务器错误: {str(e)}'}, 500

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)