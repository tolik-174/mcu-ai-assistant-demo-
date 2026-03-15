// src/extension.ts - Оновлена версія
import * as vscode from 'vscode';
import * as os from 'os';
import { spawn, execSync } from 'child_process';
import { ChatPanel } from './Chat';
import { registerInlineProvider } from './inlineProvider';

const MODEL_NAME = 'deepseek-coder:6.7b';
let ollamaProcess: any;

export function activate(context: vscode.ExtensionContext) {
    console.log('MCU Doc Assistant активується...');

    // Автоматично запускаємо Ollama якщо не запущений
    try {
        // Якщо ollama вже запущений, це не викине помилку
        execSync('curl -s http://localhost:11434', { stdio: 'ignore' });
        console.log('Ollama вже запущено');
    } catch {
        console.log(`Запускаю Ollama з моделлю ${MODEL_NAME}...`);
        ollamaProcess = spawn('ollama', ['run', MODEL_NAME], {
            detached: true,
            stdio: 'ignore'
        });
        ollamaProcess.unref();
    }

    // Ініціалізуємо inline provider
    registerInlineProvider(context);

    // Команда для відкриття чату (тепер передаємо context)
    const chatCmd = vscode.commands.registerCommand('mcu-doc-assistant.openChat', () => {
        ChatPanel.createOrShow(context.extensionUri, context);
    });
    context.subscriptions.push(chatCmd);

    // Команда для очищення історії чату (додаткова команда через палітру)
    const clearHistoryCmd = vscode.commands.registerCommand('mcu-doc-assistant.clearChatHistory', async () => {
        const confirmation = await vscode.window.showWarningMessage(
            'Are you sure you want to clear chat history?',
            { modal: true },
            'Yes, clear history',
            'Cancel'
        );

        if (confirmation === 'Yes, clear history') {
            await context.globalState.update('mcuChatHistory', []);
            vscode.window.showInformationMessage('Chat history cleared successfully');
            
            // Якщо чат відкритий, оновлюємо його
            if (ChatPanel.currentPanel) {
                ChatPanel.currentPanel.dispose();
                ChatPanel.createOrShow(context.extensionUri, context);
            }
        }
    });
    context.subscriptions.push(clearHistoryCmd);

    // Інформація про систему
    const systemInfoCmd = vscode.commands.registerCommand('mcu-doc-assistant.systemInfo', () => {
        const historyCount = context.globalState.get<any[]>('mcuChatHistory')?.length || 0;
        
        const info = `
         Система:
        - Платформа: ${os.platform()}
        - CPU: ${os.arch()}
        - Вільна пам'ять: ${(os.freemem() / 1024 / 1024).toFixed(2)} MB
        - Загальна пам'ять: ${(os.totalmem() / 1024 / 1024).toFixed(2)} MB
        
         Чат:
        - Повідомлень в історії: ${historyCount}
        - Модель: ${MODEL_NAME}
        `;
        vscode.window.showInformationMessage(info);
    });
    context.subscriptions.push(systemInfoCmd);

    // Аналіз вибраного коду
    const analyzeCodeCmd = vscode.commands.registerCommand('mcu-doc-assistant.analyzeCode', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const text = editor.document.getText(editor.selection);
            const lines = text.split('\n').length;
            const words = text.split(/\s+/).filter(w => w.length > 0).length;

            vscode.window.showInformationMessage(
                `Код:
                Рядків: ${lines}
                Слів: ${words}
                Символів: ${text.length}`
            );
        } else {
            vscode.window.showWarningMessage('Виділіть код для аналізу!');
        }
    });
    context.subscriptions.push(analyzeCodeCmd);

    // Status bar item з інформацією про історію
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    
    function updateStatusBar() {
        const historyCount = context.globalState.get<any[]>('mcuChatHistory')?.length || 0;
        statusBarItem.text = `$(rocket) MCU Tools (${historyCount} msgs)`;
        statusBarItem.tooltip = `MCU Doc Assistant - ${historyCount} messages in history`;
        // statusBarItem.command = "mcu-doc-assistant.systemInfo";
        statusBarItem.command = "mcu-doc-assistant.openChat";
        statusBarItem.text = `$(comment-discussion) MCU Chat (${historyCount})`;
        statusBarItem.tooltip = `Open MCU Chat Assistant (${historyCount} messages)`;
    }
    
    updateStatusBar();
    statusBarItem.show();

    // Оновлюємо status bar кожні 10 секунд
    const statusUpdateInterval = setInterval(updateStatusBar, 10000);
    context.subscriptions.push({
        dispose: () => clearInterval(statusUpdateInterval)
    });

    context.subscriptions.push(statusBarItem);

    // Показуємо welcome повідомлення при першому запуску
    const isFirstRun = context.globalState.get('mcuAssistantFirstRun', true);
    if (isFirstRun) {
        vscode.window.showInformationMessage(
            'Welcome to MCU Doc Assistant!',
            'Open Chat',
            'Learn More'
        ).then(selection => {
            if (selection === 'Open Chat') {
                vscode.commands.executeCommand('mcu-doc-assistant.openChat');
            } else if (selection === 'Learn More') {
                vscode.env.openExternal(vscode.Uri.parse('https://github.com/your-repo'));
            }
        });
        
        context.globalState.update('mcuAssistantFirstRun', false);
    }

    console.log('MCU Doc Assistant успішно активовано');
}

export function deactivate() {
    console.log('MCU Doc Assistant деактивується...');
    
    if (ollamaProcess) {
        try {
            process.kill(-ollamaProcess.pid); // зупиняємо процес разом із дочірніми
            console.log('Ollama зупинено');
        } catch (e) {
            console.warn('Не вдалося зупинити Ollama', e);
        }
    }
    
    console.log('MCU Doc Assistant деактивовано');
}