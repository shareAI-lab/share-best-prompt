# Manus Agent核心运转机制解读

## 1. 系统概述

Manus Agent是一个基于大型语言模型(LLM)的智能代理系统，通过定义明确的事件流和循环机制，实现复杂任务的自动化处理。它能够访问各种工具，与用户交互，并自主完成任务。

```
┌─────────────────────────────────┐
│           用户界面              │
└───────────────────┬─────────────┘
                    │
                    ▼
┌─────────────────────────────────┐
│           事件流系统            │
│                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────┐│
│  │Message  │ │Action   │ │Observation││
│  └─────────┘ └─────────┘ └─────┘│
│                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────┐│
│  │Plan     │ │Knowledge│ │Datasource││
│  └─────────┘ └─────────┘ └─────┘│
└───────────────────┬─────────────┘
                    │
                    ▼
┌─────────────────────────────────┐
│           Agent循环             │
│                                 │
│  1. 分析事件                    │
│  2. 选择工具                    │
│  3. 执行与观察                  │
│  4. 迭代                        │
└───────────────────┬─────────────┘
                    │
                    ▼
┌─────────────────────────────────┐
│           工具执行层            │
│                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────┐│
│  │文件工具 │ │Shell工具│ │浏览器工具││
│  └─────────┘ └─────────┘ └─────┘│
│                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────┐│
│  │消息工具 │ │数据工具 │ │其他工具││
│  └─────────┘ └─────────┘ └─────┘│
└─────────────────────────────────┘
```

## 2. 事件流系统

事件流是Manus Agent的"神经系统"，负责记录和传递系统中的所有信息。

### 2.1 核心事件类型

事件流由六种基本事件类型组成：

1. **Message事件**：用户输入的消息，触发Agent的任务处理
2. **Action事件**：Agent决定执行的工具调用，包含工具名称和参数
3. **Observation事件**：工具执行后的结果，反馈给Agent
4. **Plan事件**：任务规划信息，指导Agent的整体行动
5. **Knowledge事件**：向Agent提供的知识片段，辅助决策
6. **Datasource事件**：数据源信息，提供外部数据访问方式

### 2.2 事件结构示例

每种事件类型都有特定的结构。以下是典型事件的JSON结构示例：

```json
// Message事件示例
{
  "type": "Message", 
  "role": "user", 
  "timestamp": "2023-05-01T14:30:45Z", 
  "content": "请帮我创建一个简单的网站"
}

// Action事件示例
{
  "type": "Action", 
  "role": "assistant", 
  "timestamp": "2023-05-01T14:30:50Z", 
  "tool_calls": [{
    "id": "call_001", 
    "name": "message_notify_user", 
    "arguments": {
      "text": "好的，我将帮您创建一个简单的网站。"
    }
  }]
}

// Observation事件示例
{
  "type": "Observation", 
  "role": "tool", 
  "timestamp": "2023-05-01T14:30:52Z", 
  "tool_call_id": "call_001", 
  "name": "message_notify_user", 
  "status": "success", 
  "result": "Notification sent."
}

// Plan事件示例
{
  "type": "Plan", 
  "timestamp": "2023-05-01T14:31:00Z", 
  "plan_id": "plan_001", 
  "step": 1, 
  "total_steps": 5, 
  "status": "in_progress", 
  "pseudocode": "1. 确定网站需求\n2. 创建HTML文件\n3. 添加CSS样式\n4. 添加JavaScript功能\n5. 测试网站", 
  "reflection": "这是一个创建基本网站的计划，从需求分析到最终测试。"
}
```

### 2.3 事件流管理伪代码

```python
class EventStream:
    def __init__(self, max_context_length=10000):
        self.events = []
        self.max_context_length = max_context_length
        
    def add_event(self, event):
        """添加新事件到事件流"""
        self.events.append(event)
        self._manage_context_length()
        
    def get_recent_events(self, n=None):
        """获取最近的n个事件，如不指定则返回全部"""
        if n is None:
            return self.events
        return self.events[-n:]
    
    def get_events_by_type(self, event_type):
        """按类型获取事件"""
        return [e for e in self.events if e["type"] == event_type]
    
    def _manage_context_length(self):
        """管理上下文长度，避免超出LLM的token限制"""
        if self._calculate_token_length() > self.max_context_length:
            # 简单策略：保留最新的事件
            self.events = self.events[-int(self.max_context_length/2):]
            
            # 更复杂的策略可能包括：
            # 1. 保留所有Plan事件
            # 2. 保留最近的Message事件
            # 3. 对旧事件进行摘要
            
    def _calculate_token_length(self):
        """计算当前事件流的token长度"""
        # 实际实现会使用tokenizer来计算
        return sum(len(str(e)) for e in self.events)
```

## 3. Agent循环机制

Agent循环是Manus系统的"心脏"，定义了Agent如何迭代处理任务。

### 3.1 循环步骤详解

1. **分析事件**：
   - 检查最新用户消息，理解任务需求
   - 分析工具执行结果，了解当前状态
   - 参考Plan事件，明确当前任务步骤
   - 考虑Knowledge和Datasource信息

2. **选择工具**：
   - 根据当前状态和任务目标选择合适的工具
   - 确定工具参数，准备执行
   - 遵循相关规则约束（如消息规则、浏览器规则等）

3. **执行与观察**：
   - 工具在沙箱环境中执行
   - 捕获执行结果，生成Observation事件
   - 将Observation添加到事件流

4. **迭代**：
   - 循环返回到"分析事件"步骤
   - 每轮只选择一个（或一组相关的）工具调用
   - 持续迭代直到任务完成

### 3.2 Agent循环伪代码

```python
class ManusAgent:
    def __init__(self, llm_service, event_stream, tools, sandbox):
        self.llm_service = llm_service
        self.event_stream = event_stream
        self.tools = tools
        self.sandbox = sandbox
        
    def run(self):
        """运行Agent主循环"""
        while True:
            # 1. 分析事件
            context = self._analyze_events()
            
            # 检查是否需要结束循环
            if self._should_idle(context):
                self._call_tool("idle", {})
                break
                
            # 2. 选择工具
            tool_name, tool_args = self._select_tool(context)
            
            # 3. 执行工具并观察结果
            observation = self._execute_tool(tool_name, tool_args)
            
            # 4. 添加观察结果到事件流
            self.event_stream.add_event(observation)
            
            # 循环继续...
    
    def _analyze_events(self):
        """分析事件流，提取相关上下文"""
        recent_events = self.event_stream.get_recent_events()
        # 使用LLM处理和理解事件
        return self.llm_service.process_events(recent_events)
    
    def _select_tool(self, context):
        """根据上下文选择合适的工具"""
        tool_selection = self.llm_service.select_tool(
            context=context,
            available_tools=self.tools
        )
        return tool_selection["name"], tool_selection["arguments"]
    
    def _execute_tool(self, tool_name, tool_args):
        """在沙箱环境中执行工具调用"""
        # 创建Action事件
        action = {
            "type": "Action",
            "role": "assistant",
            "timestamp": self._current_time(),
            "tool_calls": [{
                "id": self._generate_id(),
                "name": tool_name,
                "arguments": tool_args
            }]
        }
        
        # 将Action添加到事件流
        self.event_stream.add_event(action)
        
        # 在沙箱中执行工具
        result = self.sandbox.execute_tool(
            tool_name=tool_name,
            tool_args=tool_args,
            tool_call_id=action["tool_calls"][0]["id"]
        )
        
        # 创建Observation事件
        observation = {
            "type": "Observation",
            "role": "tool",
            "timestamp": self._current_time(),
            "tool_call_id": action["tool_calls"][0]["id"],
            "name": tool_name,
            "status": result["status"],
            "result": result["output"]
        }
        
        return observation
    
    def _should_idle(self, context):
        """判断是否应该进入空闲状态"""
        # 判断任务是否完成或用户是否请求停止
        return self.llm_service.should_idle(context)
    
    def _current_time(self):
        """获取当前时间戳"""
        return datetime.now().isoformat()
    
    def _generate_id(self):
        """生成唯一ID"""
        return f"call_{uuid.uuid4().hex[:8]}"
```

## 4. Planner模块

Planner是Manus系统的"战略大脑"，负责高层次任务规划。

### 4.1 功能与作用

- 将复杂任务分解为可执行的步骤序列
- 生成结构化的伪代码规划
- 在任务目标变更时更新规划
- 对任务执行进行反思和调整

### 4.2 工作机制

Planner通过向事件流注入Plan事件来工作。它在以下情况下会触发：

- 新任务启动时
- 任务目标变更时
- 执行环境发生重大变化时
- 执行过程与规划产生重大偏差时

### 4.3 Planner模块伪代码

```python
class Planner:
    def __init__(self, llm_service, event_stream):
        self.llm_service = llm_service
        self.event_stream = event_stream
        self.current_plan = None
        
    def monitor_and_plan(self):
        """监控事件流并在需要时生成或更新计划"""
        # 获取最新事件
        recent_events = self.event_stream.get_recent_events(50)
        
        # 如果没有当前计划，检查是否需要生成新计划
        if not self.current_plan:
            if self._needs_new_plan(recent_events):
                new_plan = self._generate_plan(recent_events)
                self.event_stream.add_event(new_plan)
                self.current_plan = new_plan
                self._create_todo_file(new_plan)
                return
        
        # 检查是否需要更新现有计划
        if self._needs_plan_update(recent_events, self.current_plan):
            updated_plan = self._update_plan(recent_events, self.current_plan)
            self.event_stream.add_event(updated_plan)
            self.current_plan = updated_plan
            self._update_todo_file(updated_plan)
            
    def _needs_new_plan(self, events):
        """判断是否需要生成新计划"""
        # 检查是否有新的用户消息且没有现有计划
        user_messages = [e for e in events if e["type"] == "Message" and e["role"] == "user"]
        if not user_messages:
            return False
            
        # 使用LLM判断最新用户消息是否需要规划
        latest_message = user_messages[-1]
        decision = self.llm_service.generate(
            prompt=f"以下用户消息是否需要多步骤规划来完成？\n{latest_message['content']}",
            temperature=0.1
        )
        
        return "是" in decision or "yes" in decision.lower()
    
    def _generate_plan(self, events):
        """生成新的任务规划"""
        # 提取相关上下文
        context = self._extract_planning_context(events)
        
        # 使用LLM生成规划
        plan_content = self.llm_service.generate(
            prompt=self._create_planning_prompt(context),
            temperature=0.2
        )
        
        # 解析规划内容
        steps = self._parse_steps(plan_content)
        reflection = self._extract_reflection(plan_content)
        
        # 创建Plan事件
        plan = {
            "type": "Plan",
            "timestamp": datetime.now().isoformat(),
            "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
            "step": 1,
            "total_steps": len(steps),
            "status": "in_progress",
            "pseudocode": "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)]),
            "reflection": reflection
        }
        
        return plan
    
    def _create_todo_file(self, plan):
        """根据规划创建todo.md文件"""
        steps = plan["pseudocode"].split("\n")
        todo_content = "\n".join([f"- [ ] {step[step.find('.')+1:].strip()}" for step in steps])
        
        # 这里假设有file_write工具可用
        from tools import file_write
        file_write(file="/home/ubuntu/todo.md", content=todo_content)
```

## 5. Knowledge和Datasource模块

这两个模块为Agent提供决策所需的知识和数据支持。

### 5.1 Knowledge模块

Knowledge模块向Agent提供与任务相关的知识和最佳实践。

#### 5.1.1 Knowledge模块伪代码

```python
class KnowledgeModule:
    def __init__(self, llm_service, event_stream, knowledge_base):
        self.llm_service = llm_service
        self.event_stream = event_stream
        self.knowledge_base = knowledge_base
        
    def monitor_and_provide_knowledge(self):
        """监控事件流并在需要时提供知识"""
        # 获取最新事件
        recent_events = self.event_stream.get_recent_events(30)
        
        # 判断是否需要提供知识
        knowledge_needed = self._needs_knowledge(recent_events)
        if not knowledge_needed:
            return
            
        # 生成知识查询
        query = self._generate_knowledge_query(recent_events)
        
        # 从知识库检索相关知识
        knowledge_entries = self.knowledge_base.search(query, top_k=3)
        
        if not knowledge_entries:
            return
            
        # 整合知识并创建Knowledge事件
        knowledge_event = {
            "type": "Knowledge",
            "timestamp": datetime.now().isoformat(),
            "knowledge_id": f"k_{uuid.uuid4().hex[:8]}",
            "content": self._format_knowledge(knowledge_entries),
            "source": "knowledge_base"
        }
        
        # 添加到事件流
        self.event_stream.add_event(knowledge_event)
        
    def _needs_knowledge(self, events):
        """判断当前任务是否需要知识支持"""
        # 提取任务上下文
        context = self._extract_task_context(events)
        
        # 使用LLM判断是否需要知识支持
        decision = self.llm_service.generate(
            prompt=f"基于以下任务上下文，是否需要提供额外知识来帮助完成任务？\n{context}",
            temperature=0.1
        )
        
        return "是" in decision or "yes" in decision.lower()
```

### 5.2 Datasource模块

Datasource模块负责管理对外部数据源的访问。

#### 5.2.1 Datasource模块伪代码

```python
class DatasourceModule:
    def __init__(self, llm_service, event_stream, api_registry):
        self.llm_service = llm_service
        self.event_stream = event_stream
        self.api_registry = api_registry
        
    def monitor_and_provide_datasources(self):
        """监控事件流并在需要时提供数据源信息"""
        # 获取最新事件
        recent_events = self.event_stream.get_recent_events(30)
        
        # 判断是否需要提供数据源信息
        datasource_needed = self._needs_datasource(recent_events)
        if not datasource_needed:
            return
            
        # 识别所需的数据API
        needed_apis = self._identify_needed_apis(recent_events)
        
        for api in needed_apis:
            # 获取API信息
            api_info = self.api_registry.get_api_info(api)
            
            if not api_info:
                continue
                
            # 创建Datasource事件
            datasource_event = {
                "type": "Datasource",
                "timestamp": datetime.now().isoformat(),
                "datasource_id": f"ds_{uuid.uuid4().hex[:8]}",
                "api_name": api,
                "documentation": api_info["documentation"],
                "endpoints": api_info["endpoints"]
            }
            
            # 添加到事件流
            self.event_stream.add_event(datasource_event)
```

## 6. 工具执行系统

工具是Agent与外部世界交互的桥梁，定义了Agent的能力边界。

### 6.1 工具类型概览

Manus Agent支持多种类型的工具：

- **文件工具**：文件读写、查找、替换等操作
- **Shell工具**：执行命令、与进程交互等
- **浏览器工具**：网页导航、点击、输入等
- **消息工具**：向用户发送通知、询问等
- **其他工具**：数据库操作、API调用等

### 6.2 工具执行机制

工具执行系统负责在沙箱环境中安全地执行Agent选择的工具，并将结果反馈给Agent。

#### 6.2.1 工具执行伪代码

```python
class ToolExecutor:
    def __init__(self, sandbox_environment):
        self.sandbox = sandbox_environment
        self.tools = self._load_available_tools()
        
    def execute_tool(self, tool_name, tool_args, tool_call_id):
        """执行指定的工具调用"""
        # 验证工具是否存在
        if tool_name not in self.tools:
            return {
                "status": "error",
                "output": f"Tool '{tool_name}' not found"
            }
            
        # 验证参数
        validation_result = self._validate_args(tool_name, tool_args)
        if not validation_result["valid"]:
            return {
                "status": "error",
                "output": f"Invalid arguments: {validation_result['message']}"
            }
            
        # 在沙箱中执行工具
        try:
            tool_function = self.tools[tool_name]
            result = tool_function(self.sandbox, **tool_args)
            
            return {
                "status": "success",
                "output": result
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"Execution error: {str(e)}"
            }
    
    def _validate_args(self, tool_name, args):
        """验证工具参数是否符合要求"""
        tool_schema = self._get_tool_schema(tool_name)
        # 省略具体验证逻辑
        return {"valid": True, "message": ""}
```

### 6.3 异步工具和长时间运行工具

对于异步或长时间运行的工具（如shell_exec启动的进程），Manus有专门的处理机制：

```python
class AsyncToolHandler:
    def __init__(self, event_stream):
        self.event_stream = event_stream
        self.running_processes = {}
        
    def start_process(self, process_id, command):
        """启动一个长时间运行的进程"""
        # 实际实现会在沙箱中启动进程
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.running_processes[process_id] = {
            "process": process,
            "command": command,
            "start_time": time.time()
        }
        
        return {
            "status": "running",
            "result": f"process_id: {process_id}"
        }
        
    def check_process(self, process_id):
        """检查进程状态和输出"""
        if process_id not in self.running_processes:
            return {
                "status": "error",
                "result": f"Process {process_id} not found"
            }
            
        process_info = self.running_processes[process_id]
        process = process_info["process"]
        
        # 检查进程是否仍在运行
        if process.poll() is None:
            # 进程仍在运行，获取当前输出
            output = self._read_process_output(process)
            return {
                "status": "running",
                "result": output
            }
        else:
            # 进程已结束，获取完整输出和退出码
            output = self._read_process_output(process)
            exit_code = process.returncode
            
            # 清理进程信息
            del self.running_processes[process_id]
            
            if exit_code == 0:
                return {
                    "status": "success",
                    "result": output
                }
            else:
                return {
                    "status": "error",
                    "result": f"Process exited with code {exit_code}. Output: {output}"
                }
```

## 7. 系统运行全流程

下面是一个完整的Manus Agent系统运行流程：

```python
# 系统初始化
event_stream = EventStream()
llm_service = LLMService(model="advanced_llm")
knowledge_base = KnowledgeBase()
api_registry = APIRegistry()
sandbox = SandboxEnvironment()
tool_executor = ToolExecutor(sandbox)

# 初始化核心组件
agent = ManusAgent(llm_service, event_stream, tool_executor.tools, sandbox)
planner = Planner(llm_service, event_stream)
knowledge_module = KnowledgeModule(llm_service, event_stream, knowledge_base)
datasource_module = DatasourceModule(llm_service, event_stream, api_registry)

# 启动监控线程
def monitor_thread():
    while True:
        planner.monitor_and_plan()
        knowledge_module.monitor_and_provide_knowledge()
        datasource_module.monitor_and_provide_datasources()
        time.sleep(0.5)  # 避免过于频繁的检查

threading.Thread(target=monitor_thread, daemon=True).start()

# 启动Agent主循环
agent.run()
```

## 8. 设计理念与优势

Manus Agent的设计体现了几个核心理念：

1. **结构化解决复杂性**：
   - 通过事件流、循环、规划等机制分解复杂任务
   - 模块化设计确保系统可维护和可扩展

2. **自主决策与规划**：
   - Planner模块提供高层次任务分解
   - 循环迭代机制确保进展和适应性

3. **知识增强与数据驱动**：
   - Knowledge和Datasource模块增强决策质量
   - 多源信息融合提高任务执行效果

4. **安全与可控**：
   - 沙箱执行环境确保操作安全
   - 明确的规则约束引导Agent行为

## 9. 总结

Manus Agent是一个设计精巧的智能代理系统，通过事件流驱动、Agent循环、核心模块和工具执行等机制的协同工作，能够自主完成复杂任务。系统的模块化设计和清晰的工作流程确保了高效性和可靠性，为自动化任务执行提供了强大的框架。

---

本文档旨在简明扼要地解释Manus Agent的核心运转机制，包括系统架构、事件流、Agent循环、Planner、Knowledge和Datasource模块，以及工具执行系统等关键组件。通过伪代码示例，使读者能够更直观地理解各组件的实现原理和协作方式。 

# 注意
这里仅仅是反推外网上流传的资料去解读manus agent可能的一种设计实现方式，并不代表官方实际实现。另外，Planer，知识经验源、API数据源等监听与更新的方式也有很大优化空间，比如作为副线程以每个事件步为单位去触发（而不是AI给的固定的0.5秒时间检查注入一次），也可以直接塞入主线程的执行循环中。  

# 声明
本文由AI（谷歌的gemini-2.5-pro模型 + cursor中的claude3.7-max模型）参考外网泄漏的提示词文件夹，经过探讨生成，仅供作为启发资料进行学习参考。  

# GitHub
外网网友x1xh成功获取了v0、Manus、Cursor、Same.dev 和 Lovable 的完整官方系统提示词和内部工具。  
✨ ShareAI-Lab 对其进行了翻译（并同步官方更新），以供广大网友学习，注意：仅供学习优质的提示词撰写！  
仓库地址：
```
https://github.com/shareAI-lab/share-best-prompt
```
