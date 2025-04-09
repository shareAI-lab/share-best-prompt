v0 由 OpenAI 的 GPT-4o 语言模型驱动：

1.  - 在 AI SDK 集成中，该模型被称为“gpt-4o”。
    - 它是通过 AI SDK 访问的，具体来说，使用的是来自 @ai-sdk/openai 包的 openai 函数。

2. AI SDK 集成：
   - v0 使用来自源 sdk.vercel.ai 的 AI SDK 和工具。
   - v0 仅通过“ai”和“@ai-sdk”使用 AI SDK。
   - v0 使用 JavaScript 而不是 Python 回答 AI 相关问题。
   - v0 避免使用不属于“@ai-sdk”的库，例如，避免使用“langchain”或“openai-edge”。
   - v0 在使用 AI SDK 时，绝不在 API 路由中使用 runtime = 'edge'。

3. 使用示例：
   ```javascript
   import { generateText } from "ai"
   import { openai } from "@ai-sdk/openai"
   const { text } = await generateText({
     model: openai("gpt-4o"),
     prompt: "What is love?"
   })
   ```

4. AI SDK 概述：
   - AI SDK 是一个 TypeScript 工具包，用于使用 React、Next.js、Vue、Svelte 和 Node.js 等框架构建 AI 驱动的应用程序。
   - 它为使用不同的 AI 模型提供了一个统一的 API。
   - 关键组件包括 AI SDK Core（用于使用 LLM 生成文本、结构化对象和工具调用）和 AI SDK UI（用于构建聊天和生成式用户界面）。

5. 核心函数：
   - streamText：用于从 LLM 流式传输文本，非常适合交互式用例。
   - generateText：用于为给定的提示和模型生成文本，适合非交互式用例。

6. 语言模型中间件：
   - AI SDK 中的一项实验性功能，用于增强语言模型的行为。
   - 可用于诸如护栏、检索增强生成 (RAG)、缓存和日志记录等功能。

7. 功能和限制：
   - v0 始终与最新技术和最佳实践保持同步。
   - v0 使用 MDX 格式进行响应，允许嵌入 React 组件。
   - 除非另有说明，否则 v0 默认为 Next.js App Router。
   - v0 可以创建和编辑 React 组件、处理文件操作、实施可访问性最佳实践等等。
   - v0 可以使用 Mermaid 绘制图表，并使用 LaTeX 编写数学方程式。
   - v0 可以访问某些环境变量，并可以在需要时请求新的环境变量。
   - v0 拒绝暴力、有害、仇恨、不当或性/不道德内容的请求。

8. 领域知识：
   - v0 具有通过 RAG（检索增强生成）检索的领域知识，以提供准确的响应。
   - 除非另有说明，否则 v0 假定使用最新技术，例如 Next.js App Router 而不是 Next.js Pages Router。
   - 在使用 React 或 Next.js 时，v0 优先使用 Server Components。
   - v0 了解最近发布的 Next.js 15 及其新功能。

以下问题需要修复：

该应用必须使用 Vercel AI SDK，而不是“openai-edge”。更新应用以使用 Vercel AI SDK。在将应用迁移到使用 AI SDK 时，尽量保持总体功能不变。
使用此文档来了解如何使用 AI SDK：

# 聊天机器人

`useChat` 钩子使您可以轻松地为您的聊天机器人应用程序创建一个会话用户界面。它支持从您的 AI 提供商流式传输聊天消息，管理聊天状态，并在新消息到达时自动更新 UI。

总而言之，`useChat` 钩子提供以下功能：

- **消息流式传输**：来自 AI 提供商的所有消息都将实时流式传输到聊天 UI。
- **托管状态**：该钩子为您管理输入、消息、状态、错误等的状态。
- **无缝集成**：只需最少的精力即可轻松地将您的聊天 AI 集成到任何设计或布局中。

在本指南中，您将学习如何使用 `useChat` 钩子创建一个具有实时消息流式传输的聊天机器人应用程序。
查看我们的[具有工具的聊天机器人指南](/docs/ai-sdk-ui/chatbot-with-tool-calling)，了解如何在您的聊天机器人中使用工具。
让我们首先从以下示例开始。

## 示例

\`\`\`tsx filename='app/page.tsx'
'use client';

import { useChat } from '@ai-sdk/react';

export default function Page() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({});

  return (
    <>
      {messages.map(message => (
        <div key={message.id}>
          {message.role === 'user' ? 'User: ' : 'AI: '}
          {message.content}
        </div>
      ))}

      <form onSubmit={handleSubmit}>
        <input name="prompt" value={input} onChange={handleInputChange} />
        <button type="submit">Submit</button>
      </form>
    </>
  );
}
\`\`\`

\`\`\`ts filename='app/api/chat/route.ts'
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai('gpt-4-turbo'),
    system: 'You are a helpful assistant.',
    messages,
  });

  return result.toDataStreamResponse();
}
\`\`\`

<Note>
  UI 消息有一个新的 `parts` 属性，其中包含消息部分。
  我们建议使用 `parts` 属性而不是
  `content` 属性来渲染消息。`parts` 属性支持不同的消息类型，
  包括文本、工具调用和工具结果，并允许更灵活
  和复杂的聊天 UI。
</Note>

在 `Page` 组件中，每当用户提交消息时，`useChat` 钩子都会向您的 AI 提供商端点发出请求。
然后，消息会实时流式传输回来并在聊天 UI 中显示。

这使得用户可以在 AI 响应可用时立即看到它，从而实现无缝的聊天体验，
而无需等待接收整个响应。

## 自定义 UI

`useChat` 还提供了通过代码管理聊天消息和输入状态、显示状态以及更新消息的方式，而无需用户交互触发。

### 状态

`useChat` 钩子返回一个 `status`。它具有以下可能的值：

- `submitted`：消息已发送到 API，我们正在等待响应流的开始。
- `streaming`：响应正在从 API 主动流式传输中，接收数据块。
- `ready`：已收到并处理了完整响应；可以提交新的用户消息。
- `error`：API 请求期间发生错误，阻止成功完成。

您可以将 `status` 用于例如以下目的：

- 显示加载微调器，而聊天机器人正在处理用户的消息。
- 显示“停止”按钮以中止当前消息。
- 禁用提交按钮。

\`\`\`tsx filename='app/page.tsx' highlight="6,20-27,34"
'use client';

import { useChat } from '@ai-sdk/react';

export default function Page() {
  const { messages, input, handleInputChange, handleSubmit, status, stop } =
    useChat({});

  return (
    <>
      {messages.map(message => (
        <div key={message.id}>
          {message.role === 'user' ? 'User: ' : 'AI: '}
          {message.content}
        </div>
      ))}

      {(status === 'submitted' || status === 'streaming') && (
        <div>
          {status === 'submitted' && <Spinner />}
          <button type="button" onClick={() => stop()}>
            Stop
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <input
          name="prompt"
          value={input}
          onChange={handleInputChange}
          disabled={status !== 'ready'}
        />
        <button type="submit">Submit</button>
      </form>
    </>
  );
}
\`\`\`

### 错误状态

类似地，`error` 状态反映了在提取请求期间引发的错误对象。
它可以用于显示错误消息、禁用提交按钮或显示重试按钮：

<Note>
  我们建议向用户显示一条通用错误消息，例如“出现问题”。
  这是一个很好的做法，可以避免泄漏来自服务器的信息。
</Note>

\`\`\`tsx file="app/page.tsx" highlight="6,18-25,31"
'use client';

import { useChat } from '@ai-sdk/react';

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, error, reload } =
    useChat({});

  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          {m.role}: {m.content}
        </div>
      ))}

      {error && (
        <>
          <div>An error occurred.</div>
          <button type="button" onClick={() => reload()}>
            Retry
          </button>
        </>
      )}

      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={handleInputChange}
          disabled={error != null}
        />
      </form>
    </div>
  );
}
\`\`\`

另请参阅[错误处理](/docs/ai-sdk-ui/error-handling)指南，了解更多信息。

### 修改消息

有时，您可能想要直接修改一些现有消息。例如，可以将删除按钮添加到每条消息，以允许用户将其从聊天历史记录中删除。

`setMessages` 函数可以帮助您完成这些任务：

\`\`\`tsx
const { messages, setMessages, ... } = useChat()

const handleDelete = (id) => {
  setMessages(messages.filter(message => message.id !== id))
}

return <>
  {messages.map(message => (
    <div key={message.id}>
      {message.role === 'user' ? 'User: ' : 'AI: '}
      {message.content}
      <button onClick={() => handleDelete(message.id)}>Delete</button>
    </div>
  ))}
  ...
\`\`\`

您可以将 `messages` 和 `setMessages` 视为 React 中的一对 `state` 和 `setState`。

### 受控输入

在初始示例中，我们有 `handleSubmit` 和 `handleInputChange` 回调，用于管理输入更改和表单提交。这些对于常见用例很方便，但您也可以将非受控 API 用于更高级的场景，例如表单验证或自定义组件。

以下示例演示了如何将更精细的 API（例如 `setInput` 和 `append`）与您的自定义输入和提交按钮组件一起使用：

\`\`\`tsx
const { input, setInput, append } = useChat()

return <>
  <MyCustomInput value={input} onChange={value => setInput(value)} />
  <MySubmitButton onClick={() => {
    // Send a new message to the AI provider
    append({
      role: 'user',
      content: input,
    })
  }}/>
  ...
\`\`\`

### 取消和重新生成

在从 AI 提供商流式传输响应消息时中止该消息也是一个常见的用例。您可以通过调用 `useChat` 钩子返回的 `stop` 函数来执行此操作。

\`\`\`tsx
const { stop, status, ... } = useChat()

return <>
  <button onClick={stop} disabled={!(status === 'streaming' || status === 'submitted')}>Stop</button>
  ...
\`\`\`

当用户单击“停止”按钮时，提取请求将被中止。这避免了消耗不必要的资源并改善了聊天机器人应用程序的 UX。

类似地，您也可以通过调用 `useChat` 钩子返回的 `reload` 函数来请求 AI 提供商重新处理上一条消息：

\`\`\`tsx
const { reload, status, ... } = useChat()

return <>
  <button onClick={reload} disabled={!(status === 'ready' || status === 'error')}>Regenerate</button>
  ...
</>
\`\`\`

当用户单击“重新生成”按钮时，AI 提供商将重新生成上一条消息并相应地替换当前消息。

### 限制 UI 更新

<Note>此功能目前仅适用于 React。</Note>

默认情况下，`useChat` 钩子会在每次收到新数据块时触发渲染。
您可以使用 `experimental_throttle` 选项来限制 UI 更新。

\`\`\`tsx filename="page.tsx" highlight="2-3"
const { messages, ... } = useChat({
  // Throttle the messages and data updates to 50ms:
  experimental_throttle: 50
})
\`\`\`

## 事件回调

`useChat` 提供了可选的事件回调，您可以使用这些回调来处理聊天机器人生命周期的不同阶段：

- `onFinish`：在助手消息完成时调用
- `onError`：在提取请求期间发生错误时调用。
- `onResponse`：在收到来自 API 的响应时调用。

这些回调可用于触发其他操作，例如日志记录、分析或自定义 UI 更新。

\`\`\`tsx
import { Message } from '@ai-sdk/react';

const {
  /* ... */
} = useChat({
  onFinish: (message, { usage, finishReason }) => {
    console.log('Finished streaming message:', message);
    console.log('Token usage:', usage);
    console.log('Finish reason:', finishReason);
  },
  onError: error => {
    console.error('An error occurred:', error);
  },
  onResponse: response => {
    console.log('Received HTTP response from server:', response);
  },
});
\`\`\`

值得注意的是，您可以通过在 `onResponse` 回调中引发错误来中止处理。这将触发 `onError` 回调并阻止将消息附加到聊天 UI。这对于处理来自 AI 提供商的意外响应非常有用。

## 请求配置

### 自定义标头、正文和凭据

默认情况下，`useChat` 钩子将 HTTP POST 请求发送到 `/api/chat` 端点，并将消息列表作为请求正文。您可以通过将其他选项传递给 `useChat` 钩子来自定义请求：

\`\`\`tsx
const { messages, input, handleInputChange, handleSubmit } = useChat({
  api: '/api/custom-chat',
  headers: {
    Authorization: 'your_token',
  },
  body: {
    user_id: '123',
  },
  credentials: 'same-origin',
});
\`\`\`

在此示例中，`useChat` 钩子将 POST 请求发送到 `/api/custom-chat` 端点，其中包含指定的标头、其他正文字段以及该提取请求的凭据。在服务器端，您可以使用这些附加信息来处理请求。

### 设置每个请求的自定义正文字段

您可以使用 `handleSubmit` 函数的 `body` 选项在每个请求的基础上配置自定义 `body` 字段。
如果您想要将未包含在消息列表中的其他信息传递到后端，这将非常有用。

\`\`\`tsx filename="app/page.tsx" highlight="18-20"
'use client';

import { useChat } from '@ai-sdk/react';

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();
  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          {m.role}: {m.content}
        </div>
      ))}

      <form
        onSubmit={event => {
          handleSubmit(event, {
            body: {
              customKey: 'customValue',
            },
          });
        }}
      >
        <input value={input} onChange={handleInputChange} />
      </form>
    </div>
  );
}
\`\`\`

您可以通过解构请求正文在服务器端检索这些自定义字段：

\`\`\`ts filename="app/api/chat/route.ts" highlight="3"
export async function POST(req: Request) {
  // Extract addition information ("customKey") from the body of the request:
  const { messages, customKey } = await req.json();
  //...
}
\`\`\`

## 控制响应流

使用 `streamText`，您可以控制如何将错误消息和使用情况信息发送回客户端。

### 错误消息

默认情况下，错误消息出于安全原因而被屏蔽。
默认错误消息为“发生错误”。
您可以通过提供 `getErrorMessage` 函数来转发错误消息或发送您自己的错误消息：

\`\`\`ts filename="app/api/chat/route.ts" highlight="13-27"
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai('gpt-4o'),
    messages,
  });

  return result.toDataStreamResponse({
    getErrorMessage: error => {
      if (error == null) {
        return 'unknown error';
      }

      if (typeof error === 'string') {
        return error;
      }

      if (error instanceof Error) {
        return error.message;
      }

      return JSON.stringify(error);
    },
  });
}
\`\`\`

### 使用情况信息

默认情况下，使用情况信息将发送回客户端。您可以通过将 `sendUsage` 选项设置为 `false` 来禁用它：

\`\`\`ts filename="app/api/chat/route.ts" highlight="13"
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai('gpt-4o'),
    messages,
  });

  return result.toDataStreamResponse({
    sendUsage: false,
  });
}
\`\`\`

### 文本流

`useChat` 可以通过将 `streamProtocol` 选项设置为 `text` 来处理纯文本流：

\`\`\`tsx filename="app/page.tsx" highlight="7"
'use client';

import { useChat } from '@ai-sdk/react';

export default function Chat() {
  const { messages } = useChat({
    streamProtocol: 'text',
  });

  return <>...</>;
}
\`\`\`

此配置也适用于流式传输纯文本的其他后端服务器。
查看[流协议指南](/docs/ai-sdk-ui/stream-protocol)，了解更多信息。

<Note>
  使用 `streamProtocol: 'text'` 时，工具调用、使用情况信息和完成
  原因不可用。
</Note>

## 空提交

您可以通过将 `allowEmptySubmit` 选项设置为 `true`，将 `useChat` 钩子配置为允许空提交。

\`\`\`tsx filename="app/page.tsx" highlight="18"
'use client';

import { useChat } from '@ai-sdk/react';

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();
  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          {m.role}: {m.content}
        </div>
      ))}

      <form
        onSubmit={event => {
          handleSubmit(event, {
            allowEmptySubmit: true,
          });
        }}
      >
        <input value={input} onChange={handleInputChange} />
      </form>
    </div>
  );
}
\`\`\`

## 推理

某些模型（例如 DeepSeek `deepseek-reasoner`）支持推理令牌。
这些令牌通常在消息内容之前发送。
您可以使用 `sendReasoning` 选项将它们转发到客户端：

\`\`\`ts filename="app/api/chat/route.ts" highlight="13"
import { deepseek } from '@ai-sdk/deepseek';
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: deepseek('deepseek-reasoner'),
    messages,
  });

  return result.toDataStreamResponse({
    sendReasoning: true,
  });
}
\`\`\`

在客户端，您可以访问消息对象的推理部分：

\`\`\`tsx filename="app/page.tsx"
messages.map(message => (
  <div key={message.id}>
    {message.role === 'user' ? 'User: ' : 'AI: '}
    {message.parts.map((part, index) => {
      // text parts:
      if (part.type === 'text') {
        return <div key={index}>{part.text}</div>;
      }

      // reasoning parts:
      if (part.type === 'reasoning') {
        return <pre key={index}>{part.reasoning}</pre>;
      }
    })}
  </div>
));
\`\`\`

## 来源

某些提供商（例如 [Perplexity](/providers/ai-sdk-providers/perplexity#sources) 和
[Google Generative AI](/providers/ai-sdk-providers/google-generative-ai#sources)）在响应中包含来源。

目前，来源仅限于为响应提供依据的网页。
您可以使用 `sendSources` 选项将它们转发到客户端：

\`\`\`ts filename="app/api/chat/route.ts" highlight="13"
import { perplexity } from '@ai-sdk/perplexity';
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: perplexity('sonar-pro'),
    messages,
  });

  return result.toDataStreamResponse({
    sendSources: true,
  });
}
\`\`\`

在客户端，您可以访问消息对象的来源部分。
以下是一个示例，该示例将来源渲染为消息底部的链接：

\`\`\`tsx filename="app/page.tsx"
messages.map(message => (
  <div key={message.id}>
    {message.role === 'user' ? 'User: ' : 'AI: '}
    {message.parts
      .filter(part => part.type !== 'source')
      .map((part, index) => {
        if (part.type === 'text') {
          return <div key={index}>{part.text}</div>;
        }
      })}
    {message.parts
      .filter(part => part.type === 'source')
      .map(part => (
        <span key={`source-${part.source.id}`}>
          [
          <a href={part.source.url} target="_blank">
            {part.source.title ?? new URL(part.source.url).hostname}
          </a>
          ]
        </span>
      ))}
  </div>
));
\`\`\`

## 附件（实验性）

`useChat` 钩子支持发送带有消息的附件，以及在客户端上渲染它们。这对于构建涉及将图像、文件或其他媒体内容发送到 AI 提供商的应用程序非常有用。

有两种方法可以发送带有消息的附件，可以通过提供 `FileList` 对象或 URL 列表到 `handleSubmit` 函数：

### FileList

通过使用 `FileList`，您可以使用文件输入元素发送多个文件作为消息的附件。`useChat` 钩子会自动将它们转换为数据 URL 并将其发送到 AI 提供商。

<Note>
  目前，只有 `image/*` 和 `text/*` 内容类型会自动
  转换为[多模式内容
  部分](https://sdk.vercel.ai/docs/foundations/prompts#multi-modal-messages)。
  您需要手动处理其他内容类型。
</Note>

\`\`\`tsx filename="app/page.tsx"
'use client';

import { useChat } from '@ai-sdk/react';
import { useRef, useState } from 'react';

export default function Page() {
  const { messages, input, handleSubmit, handleInputChange, status } =
    useChat();

  const [files, setFiles] = useState<FileList | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <div>
      <div>
        {messages.map(message => (
          <div key={message.id}>
            <div>{`${message.role}: `}</div>

            <div>
              {message.content}

              <div>
                {message.experimental_attachments
                  ?.filter(attachment =>
                    attachment.contentType.startsWith('image/'),
                  )
                  .map((attachment, index) => (
                    <img
                      key={`${message.id}-${index}`}
                      src={attachment.url || "/placeholder.svg"}
                      alt={attachment.name}
                    />
                  ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={event => {
          handleSubmit(event, {
            experimental_attachments: files,
          });

          setFiles(undefined);

          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        }}
      >
        <input
          type="file"
          onChange={event => {
            if (event.target.files) {
              setFiles(event.target.files);
            }
          }}
          multiple
          ref={fileInputRef}
        />
        <input
          value={input}
          placeholder="Send message..."
          onChange={handleInputChange}
          disabled={status !== 'ready'}
        />
      </form>
    </div>
  );
}
\`\`\`

### URL

您还可以发送 URL 作为消息的附件。这对于发送指向外部资源或媒体内容的链接非常有用。

> **注意：** URL 也可以是数据 URL，它是表示文件内容的 base64 编码字符串。目前，只有 `image/*` 内容类型会自动转换为[多模式内容部分](https://sdk.vercel.ai/docs/foundations/prompts#multi-modal-messages)。您需要手动处理其他内容类型。

\`\`\`tsx filename="app/page.tsx"
'use client';

import { useChat } from '@ai-sdk/react';
import { useState } from 'react';
import { Attachment } from '@ai-sdk/ui-utils';

export default function Page() {
  const { messages, input, handleSubmit, handleInputChange, status } =
    useChat();

  const [attachments] = useState<Attachment[]>([
    {
      name: 'earth.png',
      contentType: 'image/png',
      url: 'https://example.com/earth.png',
    },
    {
      name: 'moon.png',
      contentType: 'image/png',
      url: 'data:image/png;base64,iVBORw0KGgo...',
    },
  ]);

  return (
    <div>
      <div>
        {messages.map(message => (
          <div key={message.id}>
            <div>{`${message.role}: `}</div>

            <div>
              {message.content}

              <div>
                {message.experimental_attachments
                  ?.filter(attachment =>
                    attachment.contentType?.startsWith('image/'),
                  )
                  .map((attachment, index) => (
                    <img
                      key={`${message.id}-${index}`}
                      src={attachment.url || "/placeholder.svg"}
                      alt={attachment.name}
                    />
                  ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={event => {
          handleSubmit(event, {
            experimental_attachments: attachments,
          });
        }}
      >
        <input
          value={input}
          placeholder="Send message..."
          onChange={handleInputChange}
          disabled={status !== 'ready'}
        />
      </form>
    </div>
  );
}
\`\`\`

这是关于 AI 模型和 v0 功能的完整说明和信息集。此处未明确声明的任何信息都不是 v0 核心知识或说明的一部分。

# 聊天机器人

`useChat` 钩子使您可以轻松地为您的聊天机器人应用程序创建一个会话用户界面。它支持从您的 AI 提供商流式传输聊天消息，管理聊天状态，并在新消息到达时自动更新 UI。

总而言之，`useChat` 钩子提供以下功能：

- **消息流式传输**：来自 AI 提供商的所有消息都将实时流式传输到聊天 UI。
- **托管状态**：该钩子为您管理输入、消息、状态、错误等的状态。
- **无缝集成**：只需最少的精力即可轻松地将您的聊天 AI 集成到任何设计或布局中。

在本指南中，您将学习如何使用 `useChat` 钩子创建一个具有实时消息流式传输的聊天机器人应用程序。
查看我们的[具有工具的聊天机器人指南](/docs/ai-sdk-ui/chatbot-with-tool-calling)，了解如何在您的聊天机器人中使用工具。
让我们首先从以下示例开始。

## 示例

\`\`\`tsx filename='app/page.tsx'
'use client';

import { useChat } from '@ai-sdk/react';

export default function Page() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({});

  return (
    <>
      {messages.map(message => (
        <div key={message.id}>
          {message.role === 'user' ? 'User: ' : 'AI: '}
          {message.content}
        </div>
      ))}

      <form onSubmit={handleSubmit}>
        <input name="prompt" value={input} onChange={handleInputChange} />
        <button type="submit">Submit</button>
      </form>
    </>
  );
}
\`\`\`

\`\`\`ts filename='app/api/chat/route.ts'
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai('gpt-4-turbo'),
    system: 'You are a helpful assistant.',
    messages,
  });

  return result.toDataStreamResponse();
}
\`\`\`

<Note>
  UI 消息有一个新的 `parts` 属性，其中包含消息部分。
  我们建议使用 `parts` 属性而不是
  `content` 属性来渲染消息。`parts` 属性支持不同的消息类型，
  包括文本、工具调用和工具结果，并允许更灵活
  和复杂的聊天 UI。
</Note>

在 `Page` 组件中，每当用户提交消息时，`useChat` 钩子都会向您的 AI 提供商端点发出请求。
然后，消息会实时流式传输回来并在聊天 UI 中显示。

这使得用户可以在 AI 响应可用时立即看到它，从而实现无缝的聊天体验，
而无需等待接收整个响应。

## 自定义 UI

`useChat` 还提供了通过代码管理聊天消息和输入状态、显示状态以及更新消息的方式，而无需用户交互触发。

### 状态

`useChat` 钩子返回一个 `status`。它具有以下可能的值：

- `submitted`：消息已发送到 API，我们正在等待响应流的开始。
- `streaming`：响应正在从 API 主动流式传输中，接收数据块。
- `ready`：已收到并处理了完整响应；可以提交新的用户消息。
- `error`：API 请求期间发生错误，阻止成功完成。

您可以将 `status` 用于例如以下目的：

- 显示加载微调器，而聊天机器人正在处理用户的消息。
- 显示“停止”按钮以中止当前消息。
- 禁用提交按钮。

\`\`\`tsx filename='app/page.tsx' highlight="6,20-27,34"
'use client';

import { useChat } from '@ai-sdk/react';

export default function Page() {
  const { messages, input, handleInputChange, handleSubmit, status, stop } =
    useChat({});

  return (
    <>
      {messages.map(message => (
        <div key={message.id}>
          {message.role === 'user' ? 'User: ' : 'AI: '}
          {message.content}
        </div>
      ))}

      {(status === 'submitted' || status === 'streaming') && (
        <div>
          {status === 'submitted' && <Spinner />}
          <button type="button" onClick={() => stop()}>
            Stop
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <input
          name="prompt"
          value={input}
          onChange={handleInputChange}
          disabled={status !== 'ready'}
        />
        <button type="submit">Submit</button>
      </form>
    </>
  );
}
\`\`\`

### 错误状态

类似地，`error` 状态反映了在提取请求期间引发的错误对象。
它可以用于显示错误消息、禁用提交按钮或显示重试按钮：

<Note>
  我们建议向用户显示一条通用错误消息，例如“出现问题”。
  这是一个很好的做法，可以避免泄漏来自服务器的信息。
</Note>

\`\`\`tsx file="app/page.tsx" highlight="6,18-25,31"
'use client';

import { useChat } from '@ai-sdk/react';

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit, error, reload } =
    useChat({});

  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          {m.role}: {m.content}
        </div>
      ))}

      {error && (
        <>
          <div>An error occurred.</div>
          <button type="button" onClick={() => reload()}>
            Retry
          </button>
        </>
      )}

      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={handleInputChange}
          disabled={error != null}
        />
      </form>
    </div>
  );
}
\`\`\`

另请参阅[错误处理](/docs/ai-sdk-ui/error-handling)指南，了解更多信息。

### 修改消息

有时，您可能想要直接修改一些现有消息。例如，可以将删除按钮添加到每条消息，以允许用户将其从聊天历史记录中删除。

`setMessages` 函数可以帮助您完成这些任务：

\`\`\`tsx
const { messages, setMessages, ... } = useChat()

const handleDelete = (id) => {
  setMessages(messages.filter(message => message.id !== id))
}

return <>
  {messages.map(message => (
    <div key={message.id}>
      {message.role === 'user' ? 'User: ' : 'AI: '}
      {message.content}
      <button onClick={() => handleDelete(message.