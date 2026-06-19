'use client';

import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';

interface MarkdownProps {
  content: string;
}

export default function Markdown({ content }: MarkdownProps) {
  if (!content) return null;

  // Split content by code blocks (```language ... ```)
  const parts = content.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-3 leading-relaxed text-[15px] select-text">
      {parts.map((part, index) => {
        if (part.startsWith('```')) {
          // Code Block
          const match = part.match(/```(\w*)\n([\s\S]*?)```/);
          const lang = match ? match[1] : '';
          const code = match ? match[2] : part.slice(3, -3);
          return <CodeBlock key={index} language={lang} code={code.trim()} />;
        } else {
          // Regular Markdown Text
          return <p key={index} className="whitespace-pre-line">{renderInlineMarkdown(part)}</p>;
        }
      })}
    </div>
  );
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  return (
    <div className="my-3 overflow-hidden rounded-lg border border-slate-700 bg-slate-900 text-slate-200">
      <div className="flex items-center justify-between border-b border-slate-700 bg-slate-800/80 px-4 py-1.5 text-xs text-slate-400 font-mono">
        <span>{language || 'code'}</span>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1 hover:text-slate-200 transition-colors"
        >
          {copied ? (
            <>
              <Check size={12} className="text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy size={12} />
              <span>Copy code</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-[13.5px] leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function renderInlineMarkdown(text: string) {
  if (!text) return '';

  // 1. Splitting on inline code blocks (`code`)
  const parts = text.split(/(`[^`]+`)/g);

  return parts.map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code
          key={index}
          className="mx-1 rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[13px] text-pink-400 dark:bg-slate-700 dark:text-pink-300"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // 2. Bold text parsing (**bold**)
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((subPart, subIdx) => {
      if (subPart.startsWith('**') && subPart.endsWith('**')) {
        return (
          <strong key={`${index}-${subIdx}`} className="font-semibold text-slate-100">
            {subPart.slice(2, -2)}
          </strong>
        );
      }
      return subPart;
    });
  });
}
