import * as vscode from 'vscode';

let lastSuggestion = '';

export const registerInlineProvider = (context: vscode.ExtensionContext) => {
  const provider: vscode.InlineCompletionItemProvider = {
    provideInlineCompletionItems(document, position, context, token) {
      if (!lastSuggestion) {
        return;
      }
        const range = new vscode.Range(position, position);
      return [new vscode.InlineCompletionItem(lastSuggestion, range)];
    }
  };

  context.subscriptions.push(
    vscode.languages.registerInlineCompletionItemProvider({ pattern: '**' }, provider)
  );
};

export function setInlineSuggestion(text: string) {
  lastSuggestion = text;
}




