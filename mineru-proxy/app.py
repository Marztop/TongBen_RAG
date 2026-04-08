from flask import Flask, request, jsonify, Response, render_template_string
import io
from io import BytesIO
import os
import json
from datetime import datetime
from config import Config
from logger import logger
from cache import cache
from mineru_client import client
from file_processor import processor
from model_handler import handler
from config_manager import ConfigManager

# 初始化
Config.validate()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024  # 300MB

# === 工具函数 ===

def generate_error_response(code: int, msg: str, trace_id: str = ""):
    """生成错误响应"""
    return {
        "code": code,
        "msg": msg,
        "trace_id": trace_id or "unknown"
    }

def generate_response(data=None, code: int = 0, msg: str = "ok", trace_id: str = ""):
    """生成标准响应"""
    return {
        "code": code,
        "data": data,
        "msg": msg,
        "trace_id": trace_id or datetime.now().isoformat()
    }

# === 健康检查和监控 ===

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """性能指标"""
    return jsonify({
        "cache": cache.get_stats(),
        "models": handler.get_stats()
    })

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """清空缓存"""
    cache.clear()
    return jsonify({"status": "cache cleared"})

# === 精准解析 v4 API ===

@app.route('/api/v4/extract/task', methods=['POST'])
def create_extract_task():
    """创建单文件解析任务"""
    try:
        data = request.get_json()
        url = data.get("url")
        model_version = data.get("model_version", "vlm")
        
        if not url:
            return jsonify(generate_error_response(-1, "url required", "")), 400
        
        # 验证模型
        model_version = handler.validate_model(model_version)
        
        # 移除已处理的参数
        options = {k: v for k, v in data.items() if k not in ["url", "model_version"]}
        
        # 调用官方API
        task_id = client.create_extract_task(url, model_version, **options)
        
        logger.log_info(f"Created extract task: {task_id}")
        return jsonify(generate_response({"task_id": task_id}))
    
    except Exception as e:
        logger.log_error(e, "create_extract_task")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/v4/extract/task/<task_id>', methods=['GET'])
def get_extract_task(task_id):
    """查询单个任务结果"""
    try:
        # 检查缓存
        cache_key = f"task_{task_id}"
        cached = cache.get(cache_key)
        if cached:
            logger.log_info(f"Cache hit for task {task_id}")
            return jsonify(generate_response(cached))
        
        # 调用官方API
        result = client.get_extract_task(task_id)
        
        # 缓存结果（如果完成）
        if result.get("state") == "done":
            cache.set(cache_key, result)
        
        return jsonify(generate_response(result))
    
    except Exception as e:
        logger.log_error(e, f"get_extract_task {task_id}")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/v4/extract/task/<task_id>/zip', methods=['GET'])
def download_extract_result_zip(task_id):
    """下载解析结果ZIP文件 (兼容Ragflow)"""
    try:
        # 查询任务结果
        result = client.get_extract_task(task_id)
        
        if result.get("state") != "done":
            return jsonify(generate_error_response(-1, f"Task not completed: {result.get('state')}", "")), 400
        
        zip_url = result.get("full_zip_url")
        if not zip_url:
            return jsonify(generate_error_response(-1, "No ZIP URL in result", "")), 400
        
        logger.log_info(f"Downloading ZIP file from {zip_url}")
        
        # 下载ZIP文件
        import requests as req
        response = req.get(zip_url, timeout=300, stream=True)
        response.raise_for_status()
        
        # 返回ZIP文件给客户端（作为文件流）
        logger.log_info(f"Returning ZIP file for task {task_id}")
        
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        return Response(generate(), mimetype='application/zip', headers={
            'Content-Disposition': f'attachment; filename="{task_id}.zip"'
        })
    
    except Exception as e:
        logger.log_error(e, f"download_extract_result_zip {task_id}")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/v4/file-urls/batch', methods=['POST'])
def request_batch_upload_urls():
    """申请批量上传URL"""
    try:
        data = request.get_json()
        files = data.get("files", [])
        model_version = data.get("model_version", "vlm")
        
        if not files:
            return jsonify(generate_error_response(-1, "files required", "")), 400
        
        # 验证模型
        model_version = handler.validate_model(model_version)
        
        # 移除已处理的参数
        options = {k: v for k, v in data.items() if k not in ["files", "model_version"]}
        
        # 调用官方API
        batch_id, file_urls = client.request_batch_upload_urls(files, model_version, **options)
        
        logger.log_info(f"Created batch upload: {batch_id}, {len(file_urls)} files")
        return jsonify(generate_response({
            "batch_id": batch_id,
            "file_urls": file_urls
        }))
    
    except Exception as e:
        logger.log_error(e, "request_batch_upload_urls")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/v4/extract-results/batch/<batch_id>', methods=['GET'])
def get_batch_results(batch_id):
    """获取批量任务结果"""
    try:
        # 检查缓存
        cache_key = f"batch_{batch_id}"
        cached = cache.get(cache_key)
        if cached:
            logger.log_info(f"Cache hit for batch {batch_id}")
            return jsonify(generate_response(cached))
        
        # 调用官方API
        result = client.get_batch_results(batch_id)
        
        # 缓存结果（如果全部完成）
        if all(r.get("state") == "done" for r in result.get("extract_result", [])):
            cache.set(cache_key, result)
        
        return jsonify(generate_response(result))
    
    except Exception as e:
        logger.log_error(e, f"get_batch_results {batch_id}")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/v4/extract/task/batch', methods=['POST'])
def create_batch_extract_task():
    """创建批量解析任务"""
    try:
        data = request.get_json()
        files = data.get("files", [])
        model_version = data.get("model_version", "vlm")
        
        if not files:
            return jsonify(generate_error_response(-1, "files required", "")), 400
        
        # 验证模型
        model_version = handler.validate_model(model_version)
        
        # 移除已处理的参数
        options = {k: v for k, v in data.items() if k not in ["files", "model_version"]}
        
        # 调用官方API
        batch_id = client.create_batch_extract_task(files, model_version, **options)
        
        logger.log_info(f"Created batch extract task: {batch_id}")
        return jsonify(generate_response({"batch_id": batch_id}))
    
    except Exception as e:
        logger.log_error(e, "create_batch_extract_task")
        return jsonify(generate_error_response(-1, str(e), "")), 500

# === 大文件分片处理 ===

@app.route('/api/v4/extract/file-with-chunking', methods=['POST'])
def extract_file_with_chunking():
    """
    上传并解析文件（支持大文件自动分片）
    Ragflow使用此接口上传超大PDF
    """
    try:
        if 'file' not in request.files:
            return jsonify(generate_error_response(-1, "file required", "")), 400
        
        file = request.files['file']
        model_version = request.form.get('model_version', 'vlm')
        
        if not file.filename:
            return jsonify(generate_error_response(-1, "filename required", "")), 400
        
        # 验证模型
        model_version = handler.validate_model(model_version)
        
        # 读取文件内容
        file_content = file.read()
        file_size, page_count = processor.get_pdf_info(file_content)
        
        logger.log_info(f"Received file: {file.filename}, {file_size/(1024*1024):.1f}MB, {page_count} pages")
        
        # 检查是否需要分片
        if not processor.should_split(file_size, page_count):
            # 直接上传
            batch_id, file_urls = client.request_batch_upload_urls(
                [{"name": file.filename}],
                model_version
            )
            client.upload_file(file_urls[0], file_content)
            logger.log_info(f"File uploaded without splitting: batch_id={batch_id}")
            
            return jsonify(generate_response({
                "batch_id": batch_id,
                "batch_ids": [batch_id],
                "chunks": 1,
                "info": "no splitting"
            }))
        
        # 分片处理
        chunks = processor.split_pdf(file_content)
        
        # 提交所有分片任务
        task_ids = []
        for idx, chunk_data in enumerate(chunks):
            batch_id, file_urls = client.request_batch_upload_urls(
                [{"name": f"{file.filename.split('.')[0]}_chunk_{idx}.pdf"}],
                model_version
            )
            client.upload_file(file_urls[0], chunk_data)
            task_ids.append(batch_id)
            logger.log_info(f"Uploaded chunk {idx + 1}/{len(chunks)}: batch_id={batch_id}")
        
        return jsonify(generate_response({
            "batch_ids": task_ids,
            "chunks": len(chunks),
            "info": f"file split into {len(chunks)} chunks"
        }))
    
    except Exception as e:
        logger.log_error(e, "extract_file_with_chunking")
        return jsonify(generate_error_response(-1, str(e), "")), 500

# === Agent 轻量 v1 API ===

@app.route('/api/v1/agent/parse/url', methods=['POST'])
def agent_parse_url():
    """Agent轻量API - URL解析"""
    try:
        data = request.get_json()
        url = data.get("url")
        
        if not url:
            return jsonify(generate_error_response(-1, "url required", "")), 400
        
        # 移除已处理的参数
        options = {k: v for k, v in data.items() if k != "url"}
        
        task_id = client.agent_parse_url(url, **options)
        return jsonify(generate_response({"task_id": task_id}))
    
    except Exception as e:
        logger.log_error(e, "agent_parse_url")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/v1/agent/parse/file', methods=['POST'])
def agent_parse_file():
    """Agent轻量API - 申请文件上传"""
    try:
        data = request.get_json()
        file_name = data.get("file_name")
        
        if not file_name:
            return jsonify(generate_error_response(-1, "file_name required", "")), 400
        
        # 移除已处理的参数
        options = {k: v for k, v in data.items() if k != "file_name"}
        
        task_id, file_url = client.agent_parse_file(file_name, **options)
        return jsonify(generate_response({
            "task_id": task_id,
            "file_url": file_url
        }))
    
    except Exception as e:
        logger.log_error(e, "agent_parse_file")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/v1/agent/parse/<task_id>', methods=['GET'])
def agent_get_result(task_id):
    """Agent轻量API - 查询结果"""
    try:
        # 检查缓存
        cache_key = f"agent_{task_id}"
        cached = cache.get(cache_key)
        if cached:
            return jsonify(generate_response(cached))
        
        result = client.agent_get_result(task_id)
        
        if result.get("state") == "done":
            cache.set(cache_key, result)
        
        return jsonify(generate_response(result))
    
    except Exception as e:
        logger.log_error(e, f"agent_get_result {task_id}")
        return jsonify(generate_error_response(-1, str(e), "")), 500

# === Ragflow兼容接口 (模拟本地Mineru) ===

@app.route('/file_parse', methods=['POST'])
def file_parse_ragflow_compatible():
    """
    Ragflow兼容的文件解析接口
    模拟本地Mineru的/file_parse端点
    
    接收：PDF文件上传 + 参数
    返回：ZIP文件流（直接返回官方API的解析结果）
    """
    try:
        # 检查文件
        if 'files' not in request.files:
            logger.log_error("No file provided", "file_parse_ragflow_compatible")
            return jsonify(generate_error_response(-1, "No file provided", "")), 400
        
        file = request.files['files']
        if file.filename == '':
            logger.log_error("Empty filename", "file_parse_ragflow_compatible")
            return jsonify(generate_error_response(-1, "Empty filename", "")), 400
        
        # 读取文件内容
        file_content = file.read()
        file_name = file.filename
        
        # 获取所有参数
        backend = request.form.get('backend', 'vlm')  # Ragflow使用backend参数
        all_form_data = {k: v for k, v in request.form.items()}
        
        # 记录完整的 Ragflow 请求信息
        logger.log_ragflow_request(file_name, len(file_content), backend, all_form_data)
        
        # 后端类型自动映射：将 Ragflow 的后端类型映射到官方 MinerU API 支持的模型
        def map_backend_to_version(backend_type):
            """
            将 Ragflow 后端类型映射到 MinerU API 支持的模型版本
            - pipeline → pipeline
            - vlm-http-client → MinerU-HTML
            - 其他 vlm-* → vlm
            """
            if backend_type == "pipeline":
                return "pipeline"
            elif backend_type == "vlm-http-client":
                return "MinerU-HTML"
            elif backend_type.startswith("vlm-"):
                return "vlm"
            else:
                # 默认返回原值，但记录警告
                logger.log_info(f"[Backend Mapping] 未知的后端类型: {backend_type}, 使用默认值: vlm")
                return "vlm"
        
        model_version = map_backend_to_version(backend)
        logger.log_info(f"[Backend Mapping] {backend} → {model_version}")
        
        # 第1步: 上传文件到官方API的S3 (申请上传URL)
        logger.log_info(f"[Ragflow] 第1步: 申请上传URL, batch_id 申请中...")
        try:
            batch_id, upload_urls = client.request_batch_upload_urls(
                [{"name": file_name, "size": len(file_content)}],
                model_version
            )
            logger.log_info(f"[Ragflow] 第1步成功: batch_id={batch_id}")
        except Exception as e:
            logger.log_error(e, "[Ragflow] 第1步失败 - 申请上传URL")
            raise
        
        if not upload_urls:
            err_msg = "Failed to get upload URL"
            logger.log_error(err_msg, "[Ragflow] 第1步")
            raise Exception(err_msg)
        
        upload_url = upload_urls[0]
        logger.log_info(f"[Ragflow] 第1步完成: batch_id={batch_id}, upload_url 已获取")
        
        # 第2步: 上传文件到S3
        logger.log_info(f"[Ragflow] 第2步: 上传文件到S3...")
        try:
            client.upload_file(upload_url, file_content)
            logger.log_info(f"[Ragflow] 第2步成功: 文件已上传到S3")
        except Exception as e:
            logger.log_error(e, "[Ragflow] 第2步失败 - 上传文件到S3")
            raise
        
        # 第3步: 轮询等待官方API处理
        logger.log_info(f"[Ragflow] 第3步: 开始轮询等待处理, batch_id={batch_id}")
        max_attempts = 60  # 5分钟超时
        task_result = None
        for attempt in range(max_attempts):
            try:
                result = client.get_batch_results(batch_id)
                logger.log_info(f"[Ragflow] 第3步 轮询 {attempt+1}/{max_attempts}: 已获取批量结果")
                
                # 检查批量结果中是否有完成的任务
                extract_results = result.get("extract_result", [])
                if extract_results and len(extract_results) > 0:
                    task_result = extract_results[0]
                    state = task_result.get("state")
                    
                    logger.log_info(f"[Ragflow] 任务状态: state={state}")
                    
                    if state == "done":
                        logger.log_info(f"[Ragflow] 第3步成功: 任务已完成")
                        break
                    elif state == "failed":
                        error = task_result.get("err_msg", "Unknown error")
                        err_msg = f"Task failed: {error}"
                        logger.log_error(err_msg, "[Ragflow] 第3步 - 任务失败")
                        raise Exception(err_msg)
                else:
                    logger.log_info(f"[Ragflow] 第3步 轮询 {attempt+1}/{max_attempts}: 还未有结果")
                
                if attempt % 10 == 0 and attempt > 0:
                    logger.log_info(f"[Ragflow] 第3步进行中: 已等待 {attempt*5} 秒...")
                
                import time
                time.sleep(5)
            except Exception as e:
                logger.log_error(e, f"[Ragflow] 第3步轮询异常 - 第{attempt+1}次尝试")
                raise
        else:
            err_msg = f"Task timeout after {max_attempts*5}s"
            logger.log_error(err_msg, "[Ragflow] 第3步 - 超时")
            raise Exception(err_msg)
        
        # 第4步: 下载ZIP文件
        if not task_result:
            err_msg = "Task result is empty"
            logger.log_error(err_msg, "[Ragflow] 第4步")
            raise Exception(err_msg)
        
        zip_url = task_result.get("full_zip_url") or result.get("full_zip_url")
        if not zip_url:
            err_msg = "No ZIP URL in result"
            logger.log_error(err_msg, "[Ragflow] 第4步")
            raise Exception(err_msg)
        
        logger.log_info(f"[Ragflow] 第4步: 从官方API下载ZIP文件...")
        try:
            import requests as req
            response = req.get(zip_url, timeout=300, stream=True)
            response.raise_for_status()
            zip_content = response.content
            logger.log_info(f"[Ragflow] 第4步成功: ZIP文件已下载, 大小 {len(zip_content)} 字节")
        except Exception as e:
            logger.log_error(e, "[Ragflow] 第4步失败 - 下载ZIP文件")
            raise
        
        # 第5步: 重新打包ZIP - 将UUID文件名改为PDF文件名，以适配Ragflow的期望格式
        import os
        import zipfile
        import tempfile
        import re
        import shutil
        
        cache_dir = Config.CACHE_DIR
        zip_filename = f"{batch_id}.zip"
        zip_path = os.path.join(cache_dir, zip_filename)
        
        logger.log_info(f"[Ragflow] 第5步: 重新打包ZIP文件... (file_name={file_name})")
        try:
            os.makedirs(cache_dir, exist_ok=True)
            
            # 解压原始ZIP到临时目录
            temp_extract_dir = tempfile.mkdtemp()
            logger.log_info(f"[Ragflow] 第5步: 将ZIP解压到临时目录: {temp_extract_dir}")
            
            # 先列出ZIP内容
            with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_ref:
                zip_namelist = zip_ref.namelist()
                logger.log_info(f"[Ragflow] 第5步: ZIP内文件列表 ({len(zip_namelist)}): {zip_namelist[:10]}")
                zip_ref.extractall(temp_extract_dir)
            
            # 显示解压后的所有文件和目录
            all_items = []
            for root, dirs, files in os.walk(temp_extract_dir):
                for item in dirs + files:
                    rel_path = os.path.relpath(os.path.join(root, item), temp_extract_dir)
                    all_items.append(rel_path)
            logger.log_info(f"[Ragflow] 第5步: 解压后的所有项目 ({len(all_items)}): {all_items[:15]}")
            
            # 获取PDF文件名（去掉.pdf后缀）
            pdf_base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            logger.log_info(f"[Ragflow] 第5步: 目标PDF基础名称: {pdf_base_name}")
            
            # 检测UUID前缀（从第一个文件/目录名中提取）
            uuid_prefix = None
            if all_items:
                first_item = all_items[0]
                # 尝试匹配形如 "uuid_xxx" 或 "uuid/xxx" 的模式
                match = re.match(r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', first_item)
                if match:
                    uuid_prefix = match.group(1)
                    logger.log_info(f"[Ragflow] 第5步: 检测到UUID前缀: {uuid_prefix}")
            
            if uuid_prefix:
                logger.log_info(f"[Ragflow] 第5步: 开始重命名文件，替换UUID: {uuid_prefix} → {pdf_base_name}")
                # 遍历所有文件，替换UUID前缀
                for root, dirs, files in os.walk(temp_extract_dir):
                    # 重命名目录
                    for dirname in dirs[:]:  # 使用切片创建副本，允许在迭代时修改
                        if uuid_prefix in dirname:
                            old_dir_path = os.path.join(root, dirname)
                            new_dirname = dirname.replace(uuid_prefix, pdf_base_name)
                            new_dir_path = os.path.join(root, new_dirname)
                            os.rename(old_dir_path, new_dir_path)
                            logger.log_info(f"[Ragflow] 第5步: 目录已重命名: {dirname} → {new_dirname}")
                            dirs[dirs.index(dirname)] = new_dirname  # 更新列表用于后续遍历
                    
                    # 重命名文件
                    for filename in files:
                        if uuid_prefix in filename:
                            old_file_path = os.path.join(root, filename)
                            new_filename = filename.replace(uuid_prefix, pdf_base_name)
                            new_file_path = os.path.join(root, new_filename)
                            os.rename(old_file_path, new_file_path)
                            logger.log_info(f"[Ragflow] 第5步: 文件已重命名: {filename} → {new_filename}")
            else:
                logger.log_info(f"[Ragflow] 第5步: 未检测到UUID前缀，文件结构保持不变")
            
            # 重新打包ZIP
            logger.log_info(f"[Ragflow] 第5步: 重新打包ZIP到: {zip_path}")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_extract_dir)
                        zipf.write(file_path, arcname)
            
            # 读取重新打包后的ZIP内容
            with open(zip_path, 'rb') as f:
                repacked_zip_content = f.read()
            
            # 清理临时目录
            shutil.rmtree(temp_extract_dir)
            
            logger.log_info(f"[Ragflow] 第5步成功: ZIP文件已重新打包, 新大小 {len(repacked_zip_content)} 字节")
        except Exception as e:
            logger.log_error(e, "[Ragflow] 第5步失败 - 重新打包ZIP文件")
            raise
        
        # 第6步: 返回ZIP流给Ragflow
        logger.log_info(f"[Ragflow] 第6步: 返回ZIP文件流给Ragflow客户端")
        
        def generate_zip_stream():
            yield repacked_zip_content
            logger.log_info(f"[Ragflow] 完成: ZIP文件已返回给Ragflow")
        
        return Response(
            generate_zip_stream(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{zip_filename}"'
            }
        )
    
    except Exception as e:
        logger.log_error(e, "file_parse_ragflow_compatible - 整个流程")
        return jsonify(generate_error_response(-1, str(e), "")), 500

# === 系统配置界面 ===

@app.route('/config/', methods=['GET'])
def config_page():
    """配置管理页面 - 可以设置 API Key 和 PDF 分片参数"""
    with open('templates/config.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return render_template_string(html_content)

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置（不包含 API Key）"""
    try:
        config = ConfigManager.get_all_config()
        return jsonify(generate_response(config))
    except Exception as e:
        logger.log_error(e, "get_config")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    try:
        data = request.get_json()
        
        # 记录接收到的完整请求
        logger.log_info(f"Received config update request: {json.dumps(data)}")
        
        # 更新 API Key
        if "api_key" in data:
            key = data.get("api_key", "").strip()
            if key:
                logger.log_info(f"Updating API Key: {key}")
                ConfigManager.set_api_key(key)
                logger.log_info("API Key updated successfully")
            elif not ConfigManager.has_api_key():
                # 如果新 key 为空且没有旧 key，则不操作
                pass
        
        # 更新分片配置
        if "pdf_chunking" in data:
            chunking = data.get("pdf_chunking", {})
            ConfigManager.set_chunking_config(chunking)
            logger.log_info("PDF chunking config updated")
        
        config = ConfigManager.get_all_config()
        return jsonify(generate_response(config))
    except Exception as e:
        logger.log_error(e, "update_config")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/config/test-key', methods=['POST'])
def test_api_key():
    """测试 API Key 是否有效"""
    try:
        key = ConfigManager.get_api_key()
        if not key:
            return jsonify(generate_error_response(-1, "No API Key configured", "")), 400
        
        # 测试连接到官方 API
        import requests as req
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        
        # 调用一个简单的 API 端点来测试连接（使用 PDF 文件类型）
        response = req.post(
            f"{Config.MINERU_API_URL}/api/v4/file-urls/batch",
            json={"files": [{"name": "test.pdf", "size": 1024}], "model_version": "vlm"},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                logger.log_info("API Key test successful")
                return jsonify(generate_response({"success": True, "msg": "API Key is valid"}))
            else:
                logger.log_info(f"API Key test failed: {result.get('msg')}")
                return jsonify(generate_error_response(-1, result.get("msg", "API error"), "")), 400
        else:
            logger.log_info(f"API Key test failed: HTTP {response.status_code}")
            return jsonify(generate_error_response(-1, f"HTTP {response.status_code}", "")), 400
    except Exception as e:
        logger.log_error(e, "test_api_key")
        return jsonify(generate_error_response(-1, str(e), "")), 500

# === API Key 管理 (保持向后兼容) ===

@app.route('/key/', methods=['GET'])
def key_management_page():
    """API Key 管理前端页面"""
    with open('templates/key_management.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    return render_template_string(html_content)

@app.route('/api/key', methods=['GET'])
def get_api_key_endpoint():
    """获取 API Key 信息"""
    try:
        key = ConfigManager.get_api_key()
        has_key = ConfigManager.has_api_key()
        
        return jsonify(generate_response({
            "key": key,  # 返回完整的 API Key
            "has_key": has_key,
            "configured": has_key
        }))
    except Exception as e:
        logger.log_error(e, "get_api_key_endpoint")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/key', methods=['POST'])
def set_api_key_endpoint():
    """保存 API Key"""
    try:
        data = request.get_json()
        key = data.get("key", "").strip()
        
        if not key:
            return jsonify(generate_error_response(-1, "API Key cannot be empty", "")), 400
        
        if ConfigManager.set_api_key(key):
            logger.log_info("API Key updated successfully")
            return jsonify(generate_response({"success": True, "msg": "API Key saved"}))
        else:
            return jsonify(generate_error_response(-1, "Failed to save API Key", "")), 500
    
    except Exception as e:
        logger.log_error(e, "set_api_key_endpoint")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/key', methods=['DELETE'])
def delete_api_key_endpoint():
    """删除 API Key"""
    try:
        if ConfigManager.delete_api_key():
            logger.log_info("API Key deleted successfully")
            return jsonify(generate_response({"success": True, "msg": "API Key deleted"}))
        else:
            return jsonify(generate_error_response(-1, "Failed to delete API Key", "")), 500
    
    except Exception as e:
        logger.log_error(e, "delete_api_key_endpoint")
        return jsonify(generate_error_response(-1, str(e), "")), 500

@app.route('/api/key/test', methods=['POST'])
def test_api_key_endpoint():
    """测试 API Key 是否有效"""
    try:
        key = ConfigManager.get_api_key()
        if not key:
            return jsonify(generate_error_response(-1, "No API Key configured", "")), 400
        
        # 测试连接到官方 API
        import requests as req
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        
        # 调用一个简单的 API 端点来测试连接（使用 PDF 文件类型）
        response = req.post(
            f"{Config.MINERU_API_URL}/api/v4/file-urls/batch",
            json={"files": [{"name": "test.pdf", "size": 1024}], "model_version": "vlm"},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                logger.log_info("API Key test successful")
                return jsonify(generate_response({"success": True, "msg": "API Key is valid"}))
            else:
                logger.log_info(f"API Key test failed: {result.get('msg')}")
                return jsonify(generate_error_response(-1, result.get("msg", "API error"), "")), 400
        else:
            logger.log_info(f"API Key test failed: HTTP {response.status_code}")
            return jsonify(generate_error_response(-1, f"HTTP {response.status_code}", "")), 400
    
    except Exception as e:
        logger.log_error(e, "test_api_key_endpoint")
        return jsonify(generate_error_response(-1, str(e), "")), 500

# === OpenAPI 规范 (用于 Ragflow 集成) ===

@app.route('/openapi.json', methods=['GET'])
def openapi_spec():
    """返回 OpenAPI 3.0 规范"""
    # 获取完整的服务器 URL - 支持 X-Forwarded-Proto/Host 头
    protocol = request.headers.get('X-Forwarded-Proto', 'http')
    host = request.headers.get('X-Forwarded-Host', request.host)
    server_url = f"{protocol}://{host}"
    
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "MinerU Proxy API",
            "description": "Proxy service for MinerU document parsing",
            "version": "1.0.0",
            "contact": {
                "name": "MinerU Proxy",
                "url": "https://github.com/infiniflow/mineru-proxy"
            }
        },
        "servers": [
            {
                "url": server_url,
                "description": "MinerU Proxy Server"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "operationId": "healthCheck",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Server is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "timestamp": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/v4/extract/task": {
                "post": {
                    "summary": "Create extract task",
                    "operationId": "createExtractTask",
                    "tags": ["Document Extraction"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string"},
                                        "model_version": {"type": "string", "default": "vlm"}
                                    },
                                    "required": ["url"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Task created successfully"
                        }
                    }
                }
            },
            "/api/v4/extract/task/{task_id}": {
                "get": {
                    "summary": "Get extract task result",
                    "operationId": "getExtractTask",
                    "tags": ["Document Extraction"],
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Task result retrieved"
                        }
                    }
                }
            },
            "/api/v4/extract/task/{task_id}/zip": {
                "get": {
                    "summary": "Download extract result as ZIP",
                    "operationId": "downloadExtractResultZip",
                    "tags": ["Document Extraction"],
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "ZIP file download",
                            "content": {
                                "application/zip": {
                                    "schema": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/v4/file-urls/batch": {
                "post": {
                    "summary": "Request batch upload URLs",
                    "operationId": "requestBatchUploadUrls",
                    "tags": ["File Upload"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "files": {
                                            "type": "array",
                                            "items": {"type": "object"}
                                        },
                                        "model_version": {"type": "string", "default": "vlm"}
                                    },
                                    "required": ["files"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Upload URLs generated"
                        }
                    }
                }
            },
            "/api/v4/extract-results/batch/{batch_id}": {
                "get": {
                    "summary": "Get batch extraction results",
                    "operationId": "getBatchResults",
                    "tags": ["Document Extraction"],
                    "parameters": [
                        {
                            "name": "batch_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Batch results retrieved"
                        }
                    }
                }
            },
            "/file_parse": {
                "post": {
                    "summary": "Parse file (local file upload)",
                    "operationId": "fileParse",
                    "tags": ["Document Parsing"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "File parsed successfully"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "msg": {"type": "string"},
                        "trace_id": {"type": "string"}
                    }
                },
                "Response": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "data": {"type": "object"},
                        "msg": {"type": "string"},
                        "trace_id": {"type": "string"}
                    }
                }
            }
        }
    }
    
    logger.log_info("OpenAPI specification requested")
    return jsonify(spec)

# === 错误处理 ===

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    app.run(host=Config.PROXY_HOST, port=Config.PROXY_PORT, debug=False)
