from flask import Flask, request, send_file, render_template, jsonify
import os
import tempfile
from pathlib import Path
import subprocess
from werkzeug.utils import secure_filename
import logging
import re

# ===== EPUB 转换依赖 =====
try:
    from ebooklib import epub
    from weasyprint import HTML, CSS
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

ALLOWED_EXTENSIONS = {'epub', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# EPUB 转 PDF 函数（基于你的测试代码）
# ==========================================
def convert_epub_to_pdf(epub_path, pdf_path):
    """
    EPUB 转 PDF（支持 SVG 封面）
    """
    try:
        logger.info(f"📖 开始转换 EPUB: {epub_path}")
        
        if not os.path.exists(epub_path):
            logger.error(f"文件不存在: {epub_path}")
            return False

        book = epub.read_epub(epub_path)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"📂 临时目录: {temp_dir}")

            # 步骤 1: 提取图片
            image_count = 0
            for item in book.get_items():
                name = item.get_name().lower()
                media_type = item.media_type.lower() if hasattr(item, 'media_type') else ""
                
                is_image = (
                    name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg')) or 
                    'image' in media_type
                )
                
                if is_image:
                    filename = os.path.basename(item.get_name())
                    save_path = os.path.join(temp_dir, filename)
                    try:
                        with open(save_path, 'wb') as f:
                            f.write(item.get_content())
                        image_count += 1
                    except Exception:
                        pass

            logger.info(f"🖼️ 共解压 {image_count} 张图片")

            # 步骤 2: 处理 HTML
            html_parts = []
            
            css = CSS(string='''
                @page { size: A4; margin: 2cm; }
                body { font-family: "Microsoft YaHei", "SimSun", sans-serif; line-height: 1.6; }
                img { max-width: 100%; height: auto; display: block; margin: 10px auto; }
            ''')

            def fix_path_generic(match):
                full_path = match.group(1)
                
                if full_path.startswith(('http:', 'https:', 'data:')):
                    return match.group(0)
                
                filename = os.path.basename(full_path)
                return match.group(0).replace(full_path, filename)

            for item in book.get_items():
                if item.get_type() == 9 or 'html' in item.media_type:
                    try:
                        content = item.get_content().decode('utf-8')
                        
                        # 修复各种图片路径
                        content = re.sub(r'src=["\'](.*?)["\']', fix_path_generic, content)
                        content = re.sub(r'href=["\'](.*?)["\']', fix_path_generic, content)
                        content = re.sub(r'xlink:href=["\'](.*?)["\']', fix_path_generic, content)
                        
                        html_parts.append(content)
                    except Exception as e:
                        logger.warning(f"跳过章节: {e}")

            full_html = '\n'.join(html_parts)
            
            # 步骤 3: 生成 PDF
            logger.info("⚙️ 正在渲染 PDF...")
            
            HTML(string=full_html, base_url=temp_dir).write_pdf(
                pdf_path,
                stylesheets=[css],
                presentational_hints=True
            )

        if os.path.exists(pdf_path):
            size = os.path.getsize(pdf_path) / 1024 / 1024
            logger.info(f"✅ EPUB PDF 生成成功: {pdf_path} ({size:.2f} MB)")
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"❌ EPUB 转换错误: {e}")
        import traceback
        traceback.print_exc()
        return False

# ==========================================
# PPT 转 PDF 函数（LibreOffice）
# ==========================================
def convert_ppt_to_pdf(input_path, output_dir):
    """使用 LibreOffice 转换 PPT 为 PDF"""
    try:
        logger.info(f"📊 开始转换 PPT: {input_path}")
        
        if not os.path.exists(input_path):
            logger.error(f"文件不存在: {input_path}")
            return None
        
        # 检查 LibreOffice
        try:
            subprocess.run(['libreoffice', '--version'], 
                         capture_output=True, timeout=5, check=True)
        except Exception as e:
            logger.error(f"LibreOffice 未安装或无法运行: {e}")
            return None
        
        # # 转换命令
        # cmd = [
        #     'libreoffice',
        #     '--headless',
        #     '--convert-to', 'pdf',
        #     '--outdir', output_dir,
        #     input_path
        # ]

        cmd = [
            'libreoffice',
            '--headless',
            '--nologo',
            '--no-first-start-wizard',
            # 关键：指定临时配置目录，防止权限错误
            '-env:UserInstallation=file:///tmp/LibreOffice_Conversion',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            input_path
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        logger.info(f"返回码: {result.returncode}")
        logger.info(f"输出: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"错误输出: {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"转换失败，返回码: {result.returncode}")
            return None
        
        # 查找生成的 PDF
        filename = Path(input_path).stem + '.pdf'
        pdf_path = os.path.join(output_dir, filename)
        
        if os.path.exists(pdf_path):
            logger.info(f"✅ PPT PDF 生成成功: {pdf_path}")
            return pdf_path
        else:
            logger.error(f"PDF 未找到: {pdf_path}")
            logger.info(f"目录内容: {os.listdir(output_dir)}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("PPT 转换超时")
        return None
    except Exception as e:
        logger.error(f"PPT 转换异常: {e}")
        import traceback
        traceback.print_exc()
        return None

# ==========================================
# Flask 路由
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """健康检查"""
    # 检查 LibreOffice
    libreoffice_ok = False
    try:
        subprocess.run(['libreoffice', '--version'], 
                      capture_output=True, timeout=5, check=True)
        libreoffice_ok = True
    except Exception:
        pass
    
    return jsonify({
        'status': 'ok',
        'epub_support': EPUB_AVAILABLE,
        'ppt_support': libreoffice_ok,
        'features': {
            'epub': '✅' if EPUB_AVAILABLE else '❌',
            'ppt': '✅' if libreoffice_ok else '❌'
        }
    })

@app.route('/test')
def test():
    """测试端点"""
    return jsonify({
        'message': '服务正常运行',
        'max_file_size': '50MB',
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'epub_available': EPUB_AVAILABLE
    })

@app.route('/convert', methods=['POST'])
def convert():
    logger.info("="*60)
    logger.info("收到转换请求")
    
    # 验证请求
    if 'file' not in request.files:
        logger.error("没有文件上传")
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        logger.error("文件名为空")
        return jsonify({'error': '文件名为空'}), 400
    
    if not allowed_file(file.filename):
        logger.error(f"不支持的文件格式: {file.filename}")
        return jsonify({'error': '不支持的文件格式，仅支持 EPUB、PPT、PPTX'}), 400
    
    logger.info(f"处理文件: {file.filename}")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 保存上传文件
            filename = secure_filename(file.filename)
            input_path = os.path.join(tmpdir, filename)
            file.save(input_path)
            
            file_size = os.path.getsize(input_path)
            logger.info(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
            
            # 确定文件类型并转换
            ext = Path(filename).suffix.lower()
            output_filename = Path(filename).stem + '.pdf'
            pdf_path = os.path.join(tmpdir, output_filename)
            
            success = False
            
            if ext == '.epub':
                if not EPUB_AVAILABLE:
                    return jsonify({'error': 'EPUB 转换功能未启用'}), 500
                success = convert_epub_to_pdf(input_path, pdf_path)
            elif ext in ['.ppt', '.pptx']:
                result_path = convert_ppt_to_pdf(input_path, tmpdir)
                success = result_path is not None
                if success:
                    pdf_path = result_path
            else:
                return jsonify({'error': '不支持的文件类型'}), 400
            
            # 返回结果
            if success and os.path.exists(pdf_path):
                logger.info(f"✅ 转换成功: {output_filename}")
                return send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=output_filename,
                    mimetype='application/pdf'
                )
            else:
                logger.error("❌ 转换失败")
                return jsonify({
                    'error': '转换失败，请检查文件是否完整或格式正确',
                    'file_type': ext
                }), 500
                
    except Exception as e:
        logger.error(f"❌ 处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'服务器错误: {str(e)}'
        }), 500

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 文件转换服务启动")
    logger.info("="*60)
    logger.info(f"EPUB 支持: {'✅' if EPUB_AVAILABLE else '❌'}")
    
    # 检查 LibreOffice
    try:
        result = subprocess.run(['libreoffice', '--version'], 
                              capture_output=True, text=True, timeout=5)
        logger.info(f"LibreOffice: ✅ {result.stdout.strip()}")
    except Exception:
        logger.warning("LibreOffice: ❌ 未安装")
    
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"监听端口: {port}")
    logger.info("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=False)