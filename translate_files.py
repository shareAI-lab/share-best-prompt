import os
import glob
from openai import AsyncOpenAI
from pathlib import Path
import time
import asyncio
from typing import List, Tuple
import aiofiles
from tenacity import retry, stop_after_attempt, wait_exponential
import re
import tiktoken

PROMPT_PATH = "./share-best-prompt"

# API配置
API_BASE_URL = "https://api.openai.com/v1"
API_KEY = "sk-xxx"
API_MODEL = "gpt-4o"

# 翻译配置
TRANSLATION_SYSTEM_PROMPT = """你是一位Prompt提示词文档翻译专家。请将用户提供的Prompt提示词文档翻译成中文，遵循以下原则：

1. 保持专业性：准确使用中文传达原文的技术概念和专业术语
2. 自然流畅：使用地道的中文表达方式，避免生硬的直译
3. 风格统一：
   - 保持文档的语气和风格
   - 技术术语使用业内通用的中文译法
   - 【重要：严格保留原文的格式，不要删除任何markdown标记、xml标记、代码块、序号】
4. 本地化处理：
   - 将英文标点符号转换为中文标点符号
   - 适当调整语序使其符合中文表达习惯
   - 保留必要的英文专有名词
5. 确保译文：
   - 逻辑清晰，层次分明
   - 用词准确，表达专业
   - 易于理解，自然流畅
   - 【重要：完整输出原文的翻译，不要缺少任何内容】

请基于以上原则进行翻译，确保译文既专业准确，又通俗易懂。"""

# 文件配置
OUTPUT_SUFFIX = '_zh.md'
FILE_PATTERN = '**/*.txt'

# 初始化异步OpenAI客户端
client = AsyncOpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
    timeout=1200
)

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """计算文本的token数量"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        # 如果模型不在tiktoken的列表中，使用cl100k_base作为默认编码
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

def find_special_blocks(text: str) -> List[Tuple[int, int, str]]:
    """找出所有需要保持完整的特殊块（代码块、XML、Markdown等）的位置"""
    special_patterns = [
        # 代码块 ```language ... ```
        (r'```[\w-]*\n.*?```', 'code'),
        # XML标签块 <tag>...</tag>
        (r'<[^>]+>.*?</[^>]+>', 'xml'),
        # Markdown表格
        (r'\|.*?\|[\s\S]*?\n\|[-\s|]*\|[\s\S]*?\n', 'table'),
        # Markdown标题
        (r'^#{1,6}\s.*$', 'heading'),
        # Markdown列表块
        (r'(?:^[\s-]*[-\*\+]\s+.*(?:\n|$))+', 'list'),
    ]
    
    blocks = []
    for pattern, block_type in special_patterns:
        for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
            blocks.append((match.start(), match.end(), block_type))
    
    # 按开始位置排序
    return sorted(blocks, key=lambda x: x[0])

def split_text_into_chunks(text: str, max_tokens: int = 8000) -> List[str]:
    """将文本按token数量分割成块，保持特殊块的完整性"""
    chunks = []
    special_blocks = find_special_blocks(text)
    
    def add_chunk(chunk: str):
        """添加非空文本块到结果列表"""
        if chunk.strip():
            # 验证添加的块的token数量
            chunk_tokens = count_tokens(chunk)
            print(f"添加块: {chunk_tokens} tokens")
            chunks.append(chunk)
    
    # 如果没有特殊块，直接处理整个文本
    if not special_blocks:
        current_chunk = ""
        current_tokens = 0
        sentences = re.split(r'([。！？.!?\n])', text)
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            sentence_tokens = count_tokens(sentence)
            
            if current_tokens + sentence_tokens > max_tokens:
                add_chunk(current_chunk)
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += sentence
                current_tokens += sentence_tokens
            
            i += 2
        
        if current_chunk:
            add_chunk(current_chunk)
    else:
        # 处理带有特殊块的文本
        current_chunk = ""
        current_tokens = 0
        last_pos = 0
        
        for start, end, block_type in special_blocks:
            # 处理特殊块之前的文本
            if last_pos < start:
                normal_text = text[last_pos:start]
                sentences = re.split(r'([。！？.!?\n])', normal_text)
                
                i = 0
                while i < len(sentences):
                    sentence = sentences[i]
                    if i + 1 < len(sentences):
                        sentence += sentences[i + 1]
                    
                    sentence_tokens = count_tokens(sentence)
                    
                    if current_tokens + sentence_tokens > max_tokens:
                        add_chunk(current_chunk)
                        current_chunk = sentence
                        current_tokens = sentence_tokens
                    else:
                        current_chunk += sentence
                        current_tokens += sentence_tokens
                    
                    i += 2
            
            # 处理特殊块
            special_block = text[start:end]
            special_block_tokens = count_tokens(special_block)
            
            # 如果特殊块本身就超过限制
            if special_block_tokens > max_tokens:
                if current_chunk:
                    add_chunk(current_chunk)
                add_chunk(special_block)
                current_chunk = ""
                current_tokens = 0
            # 如果当前块加上特殊块会超过限制
            elif current_tokens + special_block_tokens > max_tokens:
                add_chunk(current_chunk)
                current_chunk = special_block
                current_tokens = special_block_tokens
            else:
                current_chunk += special_block
                current_tokens += special_block_tokens
            
            last_pos = end
        
        # 处理最后一段文本
        if last_pos < len(text):
            remaining_text = text[last_pos:]
            sentences = re.split(r'([。！？.!?\n])', remaining_text)
            
            i = 0
            while i < len(sentences):
                sentence = sentences[i]
                if i + 1 < len(sentences):
                    sentence += sentences[i + 1]
                
                sentence_tokens = count_tokens(sentence)
                
                if current_tokens + sentence_tokens > max_tokens:
                    add_chunk(current_chunk)
                    current_chunk = sentence
                    current_tokens = sentence_tokens
                else:
                    current_chunk += sentence
                    current_tokens += sentence_tokens
                
                i += 2
        
        if current_chunk:
            add_chunk(current_chunk)
    
    # 验证总token数
    original_tokens = count_tokens(text)
    chunks_tokens = sum(count_tokens(chunk) for chunk in chunks)
    print(f"原文tokens: {original_tokens}")
    print(f"分块后tokens: {chunks_tokens}")
    
    return chunks

async def translate_chunks(chunks: List[str], original_text: str) -> str:
    """翻译所有文本块并合并结果"""
    translated_chunks = []
    total_tokens = sum(count_tokens(chunk) for chunk in chunks)
    processed_tokens = 0
    
    for i, chunk in enumerate(chunks):
        chunk_tokens = count_tokens(chunk)
        processed_tokens += chunk_tokens
        print(f"正在翻译第 {i+1}/{len(chunks)} 个文本块 "
              f"(tokens: {chunk_tokens}, 进度: {processed_tokens}/{total_tokens})")
        
        translated_chunk = await translate_text(chunk)
        if translated_chunk:
            translated_chunks.append(translated_chunk)
        else:
            print(f"警告：第 {i+1} 个文本块翻译失败")
            with open(f"failed_chunk_{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(chunk)
    
    result = "\n".join(translated_chunks)
    
    # 验证翻译结果是否包含所有特殊块
    original_special_blocks = find_special_blocks(original_text)
    for _, _, block_type in original_special_blocks:
        if block_type == 'code' and '```' not in result:
            print("警告：翻译结果中缺少代码块！")
        elif block_type == 'xml' and '<' not in result:
            print("警告：翻译结果中缺少XML标签！")
    
    return result

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
async def translate_text(text: str) -> str:
    """异步翻译文本，带重试机制"""
    try:
        # 计算输入文本的token数量
        input_tokens = count_tokens(text)
        # 设置输出token限制为输入的2倍（因为翻译可能会导致文本膨胀）
        # 但最大不超过16k（8k输入的2倍）
        max_output_tokens = min(input_tokens * 2, 16000)
        
        response = await client.chat.completions.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"直接输出翻译后的内容，不要输出多余内容。完整输出原文的翻译，不要缺少任何内容。开始翻译：{text}"}
            ],
            max_tokens=max_output_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"翻译过程中出现错误: {e}")
        raise

async def process_file(file_path: str) -> None:
    """异步处理单个文件"""
    try:
        # 异步读取原文件
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()

        # 将文本分割成块
        chunks = split_text_into_chunks(content)
        print(f"文件 {file_path} 被分割成 {len(chunks)} 个块")
        
        # 翻译所有块
        translated_content = await translate_chunks(chunks, content)
        
        if translated_content:
            # 创建新的文件名
            output_path = str(file_path).rsplit('.', 1)[0] + OUTPUT_SUFFIX
            
            # 异步写入翻译后的内容
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(translated_content)
            
            print(f"已完成文件翻译: {file_path} -> {output_path}")
        else:
            print(f"翻译失败: {file_path}")
    
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")

async def process_files(files: List[str], semaphore: asyncio.Semaphore) -> None:
    """使用信号量控制并发处理文件"""
    tasks = []
    for file in files:
        async with semaphore:
            task = asyncio.create_task(process_file(file))
            tasks.append(task)
    await asyncio.gather(*tasks)

async def main():
    # 递归查找所有.txt文件
    txt_files = glob.glob(os.path.join(PROMPT_PATH, FILE_PATTERN), recursive=True)
    print(f"找到 {len(txt_files)} 个.txt文件需要翻译")
    
    # 创建信号量限制并发数，考虑到每个文件可能被分成多个块，适当减小并发数
    semaphore = asyncio.Semaphore(5)  # 从10改为5，避免并发请求过多
    
    # 异步处理所有文件
    await process_files(txt_files, semaphore)

if __name__ == "__main__":
    print("开始翻译")
    asyncio.run(main()) 