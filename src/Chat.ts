// // src/Chat.ts
// import * as vscode from 'vscode';
// import * as path from 'path';
// import * as fs from 'fs';
// import { setInlineSuggestion } from './inlineProvider';

// interface ChatMessage {
//   sender: string;
//   text: string;
//   timestamp: number;
// }

// interface FileChoice {
//   id: number;
//   project: string;
//   relative_path: string;
//   absolute_path: string;
// }

// export class ChatPanel {
//   public static currentPanel: ChatPanel | undefined;
//   private readonly panel: vscode.WebviewPanel;
//   private disposables: vscode.Disposable[] = [];
//   private readonly MODEL_NAME = 'mistral:latest';
//   private chatHistory: ChatMessage[] = [];
//   private readonly STORAGE_KEY = 'mcuChatHistory';

//   //  зберігаємо choices для open <id>
//   private lastFileChoices: FileChoice[] = [];

//   public static createOrShow(extensionUri: vscode.Uri, context: vscode.ExtensionContext) {
//     const column = vscode.ViewColumn.Beside;

//     if (ChatPanel.currentPanel) {
//       ChatPanel.currentPanel.panel.reveal(column);
//       return;
//     }

//     const panel = vscode.window.createWebviewPanel(
//       'mcuChat',
//       'MCU Chat Assistant',
//       column,
//       {
//         enableScripts: true,
//         localResourceRoots: [
//           vscode.Uri.joinPath(extensionUri, 'media'),
//           vscode.Uri.joinPath(extensionUri, 'webview'),
//         ],
//       }
//     );

//     ChatPanel.currentPanel = new ChatPanel(panel, extensionUri, context);
//   }

//   private constructor(
//     panel: vscode.WebviewPanel,
//     private readonly extensionUri: vscode.Uri,
//     private readonly context: vscode.ExtensionContext
//   ) {
//     this.panel = panel;

//     this.loadChatHistory();
//     this.panel.webview.html = this.getHtmlForWebview(panel.webview);

//     this.panel.onDidDispose(() => {
//       this.saveChatHistory();
//       ChatPanel.currentPanel = undefined;
//     }, null, this.disposables);

//     // ===============================
//     // Webview message handler
//     // ===============================
//     this.panel.webview.onDidReceiveMessage(async (message) => {
//       switch (message.type) {

//         // ---------------------------
//         // SEND MESSAGE
//         // ---------------------------
//         case 'sendMessage': {
//           const { text, mode } = message;

//           // open <id>
//           const openMatch = text.match(/^open\s+(\d+)(?::(\d+))?$/i);
//           if (openMatch && this.lastFileChoices.length > 0) {
//             const id = Number(openMatch[1]);
//             const line = openMatch[2] ? Number(openMatch[2]) : null;

//             const choice = this.lastFileChoices.find(c => c.id === id);

//             if (!choice) {
//               this.addMessage('🤖', ` Invalid id: ${id}`);
//               return;
//             }

//             this.panel.webview.postMessage({
//               type: 'openFile',
//               absolutePath: choice.absolute_path,
//               line
//             });

//             this.addMessage(
//               '🤖',
//               ` Opened: ${choice.project}/${choice.relative_path}`
//             );

//             this.lastFileChoices = [];
//             return;
//           }

//           this.addMessage('👤', text);

//           const reply = await this.askOllama(text, mode);
//           this.addMessage('🤖', reply);

//           // Inline code
//           const matches = reply.matchAll(/```(?:\w+)?\s*([\s\S]+?)```/g);
//           let extractedCode = '';
//           for (const m of matches) {
//             extractedCode += m[1].trim() + '\n\n';
//           }

//           if (extractedCode) {
//             setInlineSuggestion(extractedCode.trim());
//             await vscode.commands.executeCommand('workbench.action.focusActiveEditorGroup');
//             setTimeout(
//               () => vscode.commands.executeCommand('editor.action.inlineSuggest.trigger'),
//               200
//             );
//           }
//           break;
//         }

//         // ---------------------------
//         // OPEN FILE (REAL)
//         // ---------------------------
//         case 'openFile': {
//           const { absolutePath, line } = message;

//           try {
//             const uri = vscode.Uri.file(absolutePath);
//             const doc = await vscode.workspace.openTextDocument(uri);
//             const editor = await vscode.window.showTextDocument(doc, { preview: false });

//             if (typeof line === 'number' && line > 0) {
//               const pos = new vscode.Position(line - 1, 0);
//               editor.selection = new vscode.Selection(pos, pos);
//               editor.revealRange(new vscode.Range(pos, pos));
//             }
//           } catch (e) {
//             vscode.window.showErrorMessage(`Failed to open file:\n${absolutePath}`);
//           }
//           break;
//         }


//         case 'clearHistory':
//           await this.clearChatHistory();
//           break;

//         case 'webviewReady':
//           this.restoreChatHistory();
//           break;

//         default:
//           console.warn('Unknown message type:', message.type);
//       }
//     });

//     setInterval(() => this.saveChatHistory(), 30000);
//   }

//   // ===============================
//   // CHAT HELPERS
//   // ===============================
//   private addMessage(sender: string, text: string) {
//     const message: ChatMessage = { sender, text, timestamp: Date.now() };
//     this.chatHistory.push(message);
//     if (this.chatHistory.length > 100) {
//       this.chatHistory = this.chatHistory.slice(-100);
//     }

//     this.panel.webview.postMessage({
//       type: 'addMessage',
//       sender,
//       text,
//       timestamp: message.timestamp,
//       mode: 'docs',
//     });

//     this.saveChatHistory();
//   }

//   private loadChatHistory() {
//     const saved = this.context.globalState.get<ChatMessage[]>(this.STORAGE_KEY);
//     if (saved && Array.isArray(saved)) {
//       this.chatHistory = saved;
//     }
//   }

//   private saveChatHistory() {
//     this.context.globalState.update(this.STORAGE_KEY, this.chatHistory);
//   }

//   private async clearChatHistory() {
//     const confirmation = await vscode.window.showWarningMessage(
//       'Are you sure you want to clear chat history?',
//       { modal: true },
//       'Yes, clear history',
//       'Cancel'
//     );
//     if (confirmation === 'Yes, clear history') {
//       this.chatHistory = [];
//       await this.context.globalState.update(this.STORAGE_KEY, []);
//       this.panel.webview.postMessage({ type: 'clearChat' });
//     }
//   }

//   private restoreChatHistory() {
//     this.panel.webview.postMessage({
//       type: 'restoreHistory',
//       history: this.chatHistory,
//     });
//   }

//   // ===============================
//   // BACKEND CALL
//   // ===============================
//   private async askOllama(
//     userText: string,
//     mode: 'local' | 'docs' = 'local'
//   ): Promise<string> {
//     try {
//       if (mode === 'docs') {
//         const resp = await fetch('http://127.0.0.1:8000/search', {
//           method: 'POST',
//           headers: { 'Content-Type': 'application/json' },
//           body: JSON.stringify({ query: userText, lang: 'en' }),
//         });

//         const data: any = await resp.json();

//         // MULTIPLE FILES
//         if (
//           data?.status === 'multiple' ||
//           data?.status === 'multiple_exact' ||
//           data?.status === 'multiple_related'
//         ) {
//           if (Array.isArray(data.choices)) {
//             this.lastFileChoices = data.choices.map(
//               (c: any, i: number) => ({
//                 id: i,
//                 project: c.project,
//                 relative_path: c.relative_path,
//                 absolute_path: c.absolute_path,
//               })
//             );

//             let msg = 'Multiple files found:\n\n';
//             for (const c of this.lastFileChoices) {
//               msg += `[${c.id}] ${c.project}/${c.relative_path}\n`;
//             }
//             msg += '\nUse: open <id>';
//             return msg;
//           }
//         }

//         return (data?.answer || 'No relevant documentation found.').trim();
//       }

//       // LOCAL MODE
//       const resp = await fetch('http://localhost:11434/api/generate', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({
//           model: this.MODEL_NAME,
//           prompt: userText,
//           stream: false,
//         }),
//       });

//       const json = (await resp.json()) as any;
//       return (json?.response || '').trim() || 'Empty response.';
//     } catch (err: any) {
//       return `Error: ${err.message}`;
//     }
//   }

//   // ===============================
//   // HTML
//   // ===============================
//   private getHtmlForWebview(webview: vscode.Webview): string {
//     const htmlPath = path.join(this.extensionUri.fsPath, 'src/webview', 'chat.html');
//     let html = fs.readFileSync(htmlPath, 'utf8');

//     html = html.replace(/(src|href)="(.+?)"/g, (_, attr, src) => {
//       const resource = vscode.Uri.joinPath(this.extensionUri, 'webview', src);
//       return `${attr}="${webview.asWebviewUri(resource)}"`;
//     });

//     return html;
//   }

//   public dispose() {
//     this.saveChatHistory();
//     ChatPanel.currentPanel = undefined;
//     this.panel.dispose();
//     this.disposables.forEach(d => d.dispose());
//   }
// }
// src/Chat.ts
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { setInlineSuggestion } from './inlineProvider';

interface ChatMessage {
  sender: string;
  text: string;
  timestamp: number;
}

interface FileChoice {
  id: number;
  project: string;
  file: string;
  relative_path: string;
  absolute_path: string;
}
interface SourceItem {
  pdf: string;
  page: number | null;
  type: string;
  preview?: string;
}


type DocsResponse =
  | { status: 'ok'; answer?: string; type?: string; absolute_path?: string; choices?: FileChoice[]; sources?: SourceItem[] }
  | { status: 'multiple' | 'multiple_exact' | 'multiple_related'; answer: string; choices: FileChoice[]; sources?: SourceItem[] }
  | { status: 'not_found' | 'error'; answer?: string; message?: string; sources?: SourceItem[] };



export class ChatPanel {
  public static currentPanel: ChatPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];
  private readonly MODEL_NAME = 'mistral:latest';
  private chatHistory: ChatMessage[] = [];
  private readonly STORAGE_KEY = 'mcuChatHistory';

  private lastFileChoices: FileChoice[] = [];

  public static createOrShow(extensionUri: vscode.Uri, context: vscode.ExtensionContext) {
    const column = vscode.ViewColumn.Beside;

    if (ChatPanel.currentPanel) {
      try {
        ChatPanel.currentPanel.panel.reveal(column);
        return;
      } catch {
        ChatPanel.currentPanel = undefined;
      }
    }

    const panel = vscode.window.createWebviewPanel(
      'mcuChat',
      'MCU Chat Assistant',
      column,
      {
        enableScripts: true,
        // ОЦЕ ВИРІШУЄ “ЧАТ ПУСТИЙ ПІСЛЯ ПОВЕРНЕННЯ”
        retainContextWhenHidden: true,
        localResourceRoots: [
          vscode.Uri.joinPath(extensionUri, 'media'),
          vscode.Uri.joinPath(extensionUri, 'webview'),
        ],
      }
    );

    ChatPanel.currentPanel = new ChatPanel(panel, extensionUri, context);
  }

  private constructor(
    panel: vscode.WebviewPanel,
    private readonly extensionUri: vscode.Uri,
    private readonly context: vscode.ExtensionContext
  ) {
    this.panel = panel;

    this.loadChatHistory();
    this.panel.webview.html = this.getHtmlForWebview(panel.webview);

    this.panel.onDidDispose(() => {
      this.saveChatHistory();
      ChatPanel.currentPanel = undefined;
    }, null, this.disposables);

    this.panel.webview.onDidReceiveMessage(async (message) => {
      switch (message.type) {
        case 'sendMessage': {
          const mode: 'local' | 'docs' = message.mode ?? 'local';

          // якщо фронт інколи “приклеює” час-прибираємо
          const rawText: string = String(message.text ?? '');
          const text = rawText.replace(/\s*\d{1,2}:\d{2}\s*$/, '').trim();
          if (!text) {
            return;
          }
          //  open <id>
          const openMatch = text.match(/^open\s+(\d+)$/i);
          if (openMatch && this.lastFileChoices.length > 0) {
            const id = Number(openMatch[1]);
            const choice = this.lastFileChoices.find(c => c.id === id);

            if (!choice) {
              this.addMessage('🤖', ` Invalid id: ${id}`);
              return;
            }

            try {
              const uri = vscode.Uri.file(choice.absolute_path);
              const doc = await vscode.workspace.openTextDocument(uri);
              await vscode.window.showTextDocument(doc, { preview: false });
              this.addMessage('🤖', `Opened: \`${choice.project}/${choice.relative_path}\``);
            } catch {
              vscode.window.showErrorMessage(`Failed to open file:\n${choice.absolute_path}`);
            } finally {
              this.lastFileChoices = [];
            }
            return;
          }
          // звичайний флоу
          this.addMessage('👤', text);

          // const reply = await this.askOllama(text, mode);
          // this.addMessage('🤖', reply);
          let reply = '';
          if (mode === 'local') {
            reply = await this.streamLocalOllama(text);
            this.chatHistory.push({
              sender: '🤖',
              text: reply,
              timestamp: Date.now()
            });
            this.saveChatHistory();
          } else {
            reply = await this.askOllama(text, mode);
            this.addMessage('🤖', reply);
          }
          // inline code
          const matches = reply.matchAll(/```(?:\w+)?\s*([\s\S]+?)```/g);
          let extractedCode = '';
          for (const m of matches) {
            extractedCode += m[1].trim() + '\n\n';
          }
          if (extractedCode) {
            setInlineSuggestion(extractedCode.trim());
            await vscode.commands.executeCommand('workbench.action.focusActiveEditorGroup');
            setTimeout(() => vscode.commands.executeCommand('editor.action.inlineSuggest.trigger'), 200);
          }
          break;
        }

        case 'clearHistory':
          await this.clearChatHistory();
          break;

        case 'webviewReady':
          this.restoreChatHistory();
          break;

        default:
          break;
      }
    });

    setInterval(() => this.saveChatHistory(), 30000);
  }

  private addMessage(sender: string, text: string) {
    const message: ChatMessage = { sender, text, timestamp: Date.now() };
    this.chatHistory.push(message);
    if (this.chatHistory.length > 200) {
      this.chatHistory = this.chatHistory.slice(-200);
    }
    this.panel.webview.postMessage({
      type: 'addMessage',
      sender,
      text,
      timestamp: message.timestamp,
      mode: 'docs'
    });

    // як в оригіналі
    this.saveChatHistory();
  }

  private loadChatHistory() {
    try {
      const saved = this.context.globalState.get<ChatMessage[]>(this.STORAGE_KEY);
      if (saved && Array.isArray(saved)){
        this.chatHistory = saved;
      } 
    } catch {
      this.chatHistory = [];
    }
  }

  private saveChatHistory() {
    try {
      this.context.globalState.update(this.STORAGE_KEY, this.chatHistory);
    } catch {}
  }

  private restoreChatHistory() {
    this.panel.webview.postMessage({ type: 'restoreHistory', history: this.chatHistory });
  }

  private async clearChatHistory() {
    const confirmation = await vscode.window.showWarningMessage(
      'Are you sure you want to clear chat history?',
      { modal: true },
      'Yes, clear history',
      'Cancel'
    );
    if (confirmation === 'Yes, clear history') {
      this.chatHistory = [];
      await this.context.globalState.update(this.STORAGE_KEY, []);
      this.panel.webview.postMessage({ type: 'clearChat' });
      vscode.window.showInformationMessage('Chat history cleared successfully');
    }
  }
  private async streamLocalOllama(userText: string): Promise<string> {
  const messageId = `msg-${Date.now()}`;
  let fullText = '';

  this.panel.webview.postMessage({
    type: 'startStreamingMessage',
    sender: '🤖',
    messageId,
    timestamp: Date.now()
  });

  const resp = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: this.MODEL_NAME,
      prompt: userText,
      stream: true,
      options: {
        temperature: 0.2,
        repeat_penalty: 1.05,
        num_ctx: 4096
      }
    })
  });

  if (!resp.body) {
    throw new Error('No response stream from Ollama');
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();

  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        continue;
      }
      try {
        const json = JSON.parse(trimmed);
        const chunk = json.response ?? '';
        if (chunk) {
          fullText += chunk;

          this.panel.webview.postMessage({
            type: 'updateStreamingMessage',
            messageId,
            text: fullText
          });
        }
      } catch {
        // ignore broken partial json lines
      }
    }
  }

  return fullText.trim();
}
  private async askOllama(userText: string, mode: 'local' | 'docs' = 'local'): Promise<string> {
    try {
      if (mode === 'docs') {
        const resp = await fetch('http://127.0.0.1:8000/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: userText, lang: 'en' }),
        });

        const data = (await resp.json()) as DocsResponse;

        // multiple- зберігаємо choices і повертаємо markdown (таблицю)
        if ((data as any)?.choices && Array.isArray((data as any).choices)) {
          this.lastFileChoices = (data as any).choices as FileChoice[];
        }

        // single file- якщо бек дав absolute_path, відкриваємо
        if ((data as any)?.status === 'ok' && (data as any)?.absolute_path) {
          try {
            const uri = vscode.Uri.file((data as any).absolute_path);
            const doc = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(doc, { preview: false });
          } catch {}
        }

        //завжди повертаємо answer як є (markdown)
        const ans = (data as any)?.answer ?? (data as any)?.message ?? 'No relevant documentation found.';
        const sources = (data as any)?.sources as SourceItem[] | undefined;

        return (String(ans).trim() + this.formatSources(sources)).trim();
      }

      // local
      const resp = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.MODEL_NAME,
          prompt: userText,
          stream: false,
          options: { temperature: 0.2, repeat_penalty: 1.05, num_ctx: 4096 }
        })
      });

      const json = (await resp.json()) as { response?: string; message?: { content?: string } };
      const content = json.response ?? json.message?.content ?? '';
      return content.trim() || 'Empty response.';
    } catch (err: any) {
      return `Error: ${err?.message ?? String(err)}`;
    }
  }

  private getHtmlForWebview(webview: vscode.Webview): string {
    const htmlPath = path.join(this.extensionUri.fsPath, 'src/webview', 'chat.html');
    let html = fs.readFileSync(htmlPath, 'utf8');

    html = html.replace(/(src|href)="(.+?)"/g, (_, attr, src) => {
      const resource = vscode.Uri.joinPath(this.extensionUri, 'webview', src);
      return `${attr}="${webview.asWebviewUri(resource)}"`;
    });

    return html;
  }
  private formatSources(sources?: SourceItem[]): string {
    if (!sources || sources.length === 0) {
      return '';
    }
    const lines = sources.map(s => {
      const page = (s.page === null || s.page === undefined)
        ? ''
        : ` p.${s.page}`;

      const type = s.type ? ` (${s.type})` : '';

      return `- ${s.pdf}${page}${type}`;
    });

    return `\n\n---\n**Sources:**\n${lines.join('\n')}`;
  }
  public dispose() {
    this.saveChatHistory();
    ChatPanel.currentPanel = undefined;
    this.panel.dispose();

    while (this.disposables.length) {
      const d = this.disposables.pop();
      if (d) 
      {
        d.dispose();
      }
    }
  }
}
