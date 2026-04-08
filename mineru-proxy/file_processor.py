import os
import io
import zipfile
import json
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from PyPDF2 import PdfWriter, PdfReader
from config import Config
from config_manager import ConfigManager
from logger import logger

class FileProcessor:
    """PDF文件分片处理器"""
    
    @staticmethod
    def get_chunking_config():
        """获取当前的分片配置"""
        return ConfigManager.get_chunking_config()
    
    @staticmethod
    def get_pdf_info(file_content: bytes) -> Tuple[int, int]:
        """获取PDF大小和页数"""
        pdf_reader = PdfReader(io.BytesIO(file_content))
        return len(file_content), len(pdf_reader.pages)
    
    @staticmethod
    def should_split(file_size: int, page_count: int) -> bool:
        """判断是否需要分片"""
        config = FileProcessor.get_chunking_config()
        
        # 如果分片禁用，则不分片
        if not config.get("enabled", True):
            return False
        
        needs_split = (
            file_size > config.get("max_file_size", Config.MAX_FILE_SIZE) or
            page_count > config.get("max_pages", Config.MAX_PAGES)
        )
        if needs_split:
            logger.log_info(
                f"Large file detected: {file_size/(1024*1024):.1f}MB, {page_count} pages - will split"
            )
        return needs_split
    
    @staticmethod
    def split_pdf(file_content: bytes) -> List[bytes]:
        """分片PDF文件"""
        config = FileProcessor.get_chunking_config()
        
        chunk_size = config.get("chunk_size", Config.CHUNK_SIZE)
        max_pages_per_chunk = config.get("max_pages_per_chunk", Config.MAX_PAGES_PER_CHUNK)
        
        pdf_reader = PdfReader(io.BytesIO(file_content))
        total_pages = len(pdf_reader.pages)
        chunks = []
        
        current_chunk = PdfWriter()
        current_page_count = 0
        current_size_estimate = 0
        
        for page_idx, page in enumerate(pdf_reader.pages):
            current_chunk.add_page(page)
            current_page_count += 1
            
            # 页面大小估算
            page_size_estimate = len(file_content) // total_pages
            current_size_estimate += page_size_estimate
            
            # 检查是否达到分片限制
            should_chunk = (
                current_page_count >= max_pages_per_chunk or
                current_size_estimate >= chunk_size or
                page_idx == total_pages - 1
            )
            
            if should_chunk:
                # 保存分片
                chunk_buffer = io.BytesIO()
                current_chunk.write(chunk_buffer)
                chunks.append(chunk_buffer.getvalue())
                
                logger.log_info(
                    f"Created chunk {len(chunks)}: {current_page_count} pages, "
                    f"{len(chunk_buffer.getvalue())/(1024*1024):.1f}MB"
                )
                
                # 重置
                current_chunk = PdfWriter()
                current_page_count = 0
                current_size_estimate = 0
        
        logger.log_info(f"PDF split into {len(chunks)} chunks")
        return chunks
    
    @staticmethod
    def merge_results(results: List[bytes], chunk_count: int) -> bytes:
        """合并多个分片的解析结果"""
        # 创建输出ZIP
        output_buffer = io.BytesIO()
        output_zip = zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED)
        
        merged_markdown = []
        merged_content_list = []
        all_images = {}
        merged_metadata = {"total_chunks": chunk_count, "chunks": []}
        
        for chunk_idx, result_data in enumerate(results):
            logger.log_info(f"Processing chunk {chunk_idx + 1}/{len(results)}")
            
            # 读取每个分片的ZIP
            chunk_zip = zipfile.ZipFile(io.BytesIO(result_data), 'r')
            
            # 提取并合并Markdown
            for name in chunk_zip.namelist():
                if name.endswith('.md'):
                    md_content = chunk_zip.read(name).decode('utf-8')
                    merged_markdown.append(f"\n<!-- Chunk {chunk_idx + 1} -->\n")
                    merged_markdown.append(md_content)
                    break
            
            # 提取并合并content_list.json
            try:
                content_list_data = chunk_zip.read('content_list.json')
                content_list = json.loads(content_list_data)
                merged_content_list.extend(content_list)
            except KeyError:
                pass
            
            # 提取所有图片
            for name in chunk_zip.namelist():
                if name.startswith('images/'):
                    image_data = chunk_zip.read(name)
                    unique_name = f"{chunk_idx}_{name.split('/')[-1]}"
                    all_images[f"images/{unique_name}"] = image_data
            
            chunk_zip.close()
        
        # 创建合并的ZIP文件
        if merged_markdown:
            output_zip.writestr('full.md', ''.join(merged_markdown).encode('utf-8'))
        
        if merged_content_list:
            output_zip.writestr('content_list.json', 
                               json.dumps(merged_content_list, ensure_ascii=False, indent=2).encode('utf-8'))
        
        # 添加所有图片
        for img_path, img_data in all_images.items():
            output_zip.writestr(img_path, img_data)
        
        # 添加元数据
        output_zip.writestr('_merged_metadata.json',
                           json.dumps(merged_metadata, ensure_ascii=False, indent=2).encode('utf-8'))
        
        output_zip.close()
        
        result = output_buffer.getvalue()
        logger.log_info(f"Merge complete: {len(result)/(1024*1024):.1f}MB")
        return result

processor = FileProcessor()
