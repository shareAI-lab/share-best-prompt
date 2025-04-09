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

def split_text_into_chunks(text: str, max_tokens: int = 20000) -> List[str]:
    """将文本按token数量分割成块，保持特殊块的完整性"""
    # 找出所有特殊块的位置
    special_blocks = find_special_blocks(text)
    
    chunks = []
    current_chunk = ""
    current_chunk_tokens = 0
    last_pos = 0
    
    def add_chunk(chunk: str):
        if chunk.strip():
            chunks.append(chunk)
    
    for start, end, block_type in special_blocks:
        # 处理特殊块之前的普通文本
        if last_pos < start:
            normal_text = text[last_pos:start]
            sentences = re.split(r'([。！？.!?])', normal_text)
            
            for i in range(0, len(sentences)-1, 2):
                sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                sentence_tokens = count_tokens(sentence)
                
                # 如果当前块加上新句子会超过token限制
                if current_chunk_tokens + sentence_tokens > max_tokens and current_chunk:
                    add_chunk(current_chunk)
                    current_chunk = sentence
                    current_chunk_tokens = sentence_tokens
                else:
                    current_chunk += sentence
                    current_chunk_tokens += sentence_tokens
        
        # 处理特殊块
        special_block = text[start:end]
        special_block_tokens = count_tokens(special_block)
        
        # 如果特殊块本身就超过最大token限制，单独作为一个块
        if special_block_tokens > max_tokens:
            if current_chunk:
                add_chunk(current_chunk)
                current_chunk = ""
                current_chunk_tokens = 0
            add_chunk(special_block)
        # 如果当前块加上特殊块会超过token限制
        elif current_chunk_tokens + special_block_tokens > max_tokens and current_chunk:
            add_chunk(current_chunk)
            current_chunk = special_block
            current_chunk_tokens = special_block_tokens
        else:
            current_chunk += special_block
            current_chunk_tokens += special_block_tokens
        
        last_pos = end
    
    # 处理最后一段普通文本
    if last_pos < len(text):
        remaining_text = text[last_pos:]
        sentences = re.split(r'([。！？.!?])', remaining_text)
        
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
            sentence_tokens = count_tokens(sentence)
            
            if current_chunk_tokens + sentence_tokens > max_tokens and current_chunk:
                add_chunk(current_chunk)
                current_chunk = sentence
                current_chunk_tokens = sentence_tokens
            else:
                current_chunk += sentence
                current_chunk_tokens += sentence_tokens
    
    # 添加最后一个块
    if current_chunk:
        add_chunk(current_chunk)
    
    return chunks

async def translate_chunks(chunks: List[str]) -> str:
    """翻译所有文本块并合并结果"""
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_tokens = count_tokens(chunk)
        print(f"正在翻译第 {i+1}/{len(chunks)} 个文本块 (tokens: {chunk_tokens})")
        translated_chunk = await translate_text(chunk)
        if translated_chunk:
            translated_chunks.append(translated_chunk)
        else:
            print(f"警告：第 {i+1} 个文本块翻译失败")
    
    return "\n".join(translated_chunks)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
async def translate_text(text: str) -> str:
    """异步翻译文本，带重试机制"""
    try:
        # 计算输入文本的token数量
        input_tokens = count_tokens(text)
        max_output_tokens = 32768
        
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
        
        # 将文本分割成多个块
        chunks = split_text_into_chunks(content)
        print(f"文件 {file_path} 被分割成 {len(chunks)} 个块")
        
        # 翻译所有块
        translated_content = await translate_chunks(chunks)
        
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
        print(f"处理文件 {file_path} 时出错: {e}")

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
    
    # 创建信号量限制并发数
    semaphore = asyncio.Semaphore(10)
    
    # 异步处理所有文件
    await process_files(txt_files, semaphore)

if __name__ == "__main__":
    print("开始翻译")
    asyncio.run(main()) 