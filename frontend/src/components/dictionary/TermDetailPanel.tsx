/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { TermDetail } from '../../data/mockDictionaryData';
import { 
  Sparkles, 
  BookOpen, 
  ArrowRight, 
  ArrowDown, 
  Database, 
  HelpCircle, 
  Send, 
  Bot, 
  CheckCircle2, 
  Share2,
  BookmarkPlus
} from 'lucide-react';

interface TermDetailPanelProps {
  term: TermDetail;
  onSelectRelatedTerm: (termName: string) => void;
}

interface FollowUpMessage {
  id: string;
  question: string;
  answer: string;
  timestamp: string;
}

export function TermDetailPanel({
  term,
  onSelectRelatedTerm,
}: TermDetailPanelProps) {
  const [followUpInput, setFollowUpInput] = useState<string>('');
  const [isSubmittingFollowUp, setIsSubmittingFollowUp] = useState<boolean>(false);
  const [followUpHistory, setFollowUpHistory] = useState<FollowUpMessage[]>([]);
  const [copiedToast, setCopiedToast] = useState<boolean>(false);

  const handleSendFollowUp = (e: React.FormEvent) => {
    e.preventDefault();
    const query = followUpInput.trim();
    if (!query) return;

    setIsSubmittingFollowUp(true);

    setTimeout(() => {
      let mockAnswer = '';
      if (term.defaultFollowUpAnswer && query.includes(term.name)) {
        mockAnswer = term.defaultFollowUpAnswer;
      } else {
        mockAnswer = `"${term.name}" 상황에서는 심판의 즉각적인 수신호와 루상 주자들의 재빠른 리터치 판단이 가장 결정적인 포인트예요! 초보자분들은 타구가 뜬공인지 땅볼인지를 먼저 관찰하시면 상황을 한눈에 파악하실 수 있어요.`;
      }

      const newMessage: FollowUpMessage = {
        id: `fu-${Date.now()}`,
        question: query,
        answer: mockAnswer,
        timestamp: '방금 전',
      };

      setFollowUpHistory((prev) => [...prev, newMessage]);
      setFollowUpInput('');
      setIsSubmittingFollowUp(false);
    }, 450);
  };

  const handlePromptChipClick = (sampleQuestion: string) => {
    setFollowUpInput(sampleQuestion);
  };

  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col justify-between transition-all duration-300">
      
      <div>
        {/* Top Header & Tag */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-purple-700 bg-purple-100 px-2.5 py-0.5 rounded-full">
                {term.category} 용어
              </span>
              <span className="text-xs font-semibold text-gray-400">
                {term.englishName}
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight">
              {term.name}
            </h2>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-purple-50 text-purple-700 border border-purple-100 text-xs font-bold self-start sm:self-auto">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>RAG AI 실시간 해설</span>
          </div>
        </div>

        {/* 1. One-Line Summary Card */}
        <div className="mt-4 p-4 rounded-2xl bg-gradient-to-r from-purple-50/90 via-purple-50/50 to-indigo-50/40 border border-purple-200/70 text-purple-950">
          <div className="text-[11px] font-bold text-purple-600 uppercase tracking-wider mb-1">
            한 줄 핵심 요약
          </div>
          <div className="text-base sm:text-lg font-black leading-snug">
            "{term.oneLineSummary}"
          </div>
        </div>

        {/* 2. Beginner Explanation Box */}
        <div className="mt-5 text-gray-700">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1">
            <BookOpen className="w-3.5 h-3.5 text-purple-600" />
            <span>초보자 눈높이 해설</span>
          </div>
          <p className="text-sm sm:text-base leading-relaxed font-normal whitespace-pre-line text-gray-800 bg-slate-50/70 p-4 sm:p-5 rounded-2xl border border-slate-100">
            {term.beginnerExplanation}
          </p>
        </div>

        {/* 3. Game Example Flow ("경기에서는 이렇게 나와요") */}
        <div className="mt-5 p-4 sm:p-5 rounded-2xl bg-white border border-gray-200/90 shadow-xs">
          <div className="text-xs font-extrabold text-gray-700 mb-3 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-600" />
              <span>경기에서는 이렇게 나와요</span>
            </span>
            <span className="text-[11px] text-gray-400 font-normal">상황 전개 흐름</span>
          </div>

          {/* Flow Steps (Horizontal on desktop, vertical connector on mobile) */}
          <div className="flex flex-col md:flex-row items-center gap-2 md:gap-1.5 justify-between">
            {term.gameFlow.map((step, idx) => (
              <React.Fragment key={idx}>
                <div className={`w-full md:w-auto flex-1 p-2.5 rounded-xl border text-center text-xs font-bold transition-all ${
                  idx === term.gameFlow.length - 1
                    ? 'bg-purple-100 border-purple-300 text-purple-900 shadow-2xs'
                    : 'bg-gray-50 border-gray-200 text-gray-700'
                }`}>
                  <span className="text-[10px] text-gray-400 block mb-0.5">Step 0{idx + 1}</span>
                  <span className="truncate block">{step}</span>
                </div>

                {idx < term.gameFlow.length - 1 && (
                  <div className="hidden md:flex text-purple-400 shrink-0">
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                )}
                {idx < term.gameFlow.length - 1 && (
                  <div className="md:hidden text-purple-400 my-0.5">
                    <ArrowDown className="w-3.5 h-3.5" />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* 4. Related Terms Chips */}
        <div className="mt-5">
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2.5">
            같이 알아두면 좋은 용어
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {term.relatedTerms.map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectRelatedTerm(chip.replace('#', '').trim())}
                className="px-3 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold text-xs transition-colors cursor-pointer border border-purple-200/70 hover:scale-105 active:scale-95"
              >
                {chip}
              </button>
            ))}
          </div>
        </div>

        {/* 5. AI / RAG Sources Citation Box */}
        <div className="mt-5 p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
          <div className="text-xs font-extrabold text-gray-700 flex items-center justify-between mb-2 pb-1.5 border-b border-slate-200">
            <span className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-purple-600" />
              <span>이 설명은 어디에서 가져왔나요?</span>
            </span>
            <span className="text-[10px] text-purple-700 bg-purple-100/70 px-2 py-0.5 rounded font-bold">
              RAG 신뢰 검증
            </span>
          </div>

          <ul className="space-y-1.5 text-xs text-gray-600">
            {term.sources.map((src, i) => (
              <li key={i} className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 truncate">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0" />
                  <span className="font-medium text-gray-800">{src.title}</span>
                </span>
                <span className="text-[10px] text-gray-400 bg-white px-1.5 py-0.5 rounded border border-gray-200 shrink-0 ml-2">
                  {src.sourceType}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* 6. Follow-up Q&A History (Conversation log) */}
        {followUpHistory.length > 0 && (
          <div className="mt-5 space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-200">
            {followUpHistory.map((item) => (
              <div key={item.id} className="p-4 rounded-2xl bg-purple-50/80 border border-purple-200 space-y-2">
                <div className="flex items-start gap-2 text-xs font-bold text-gray-700">
                  <span className="text-purple-600">Q:</span>
                  <span>{item.question}</span>
                </div>
                <div className="flex items-start gap-2 text-xs sm:text-sm font-medium text-purple-950 bg-white p-3 rounded-xl border border-purple-100 leading-relaxed">
                  <Bot className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
                  <span>{item.answer}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 7. AI Follow-Up Question Input UI */}
      <div className="mt-6 pt-5 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs font-bold text-gray-500 mb-2">
          <span className="flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>이 용어에 대해 더 궁금한 점을 물어보세요</span>
          </span>
          {term.defaultFollowUpQuestion && (
            <button
              type="button"
              onClick={() => handlePromptChipClick(term.defaultFollowUpQuestion!)}
              className="text-[11px] text-purple-600 hover:text-purple-800 font-semibold cursor-pointer underline underline-offset-2 hidden sm:inline"
            >
              예: "{term.defaultFollowUpQuestion}"
            </button>
          )}
        </div>

        <form onSubmit={handleSendFollowUp} className="relative flex items-center">
          <input
            type="text"
            value={followUpInput}
            onChange={(e) => setFollowUpInput(e.target.value)}
            placeholder={term.defaultFollowUpQuestion || `예: ${term.name}은 언제 발생하나요?`}
            className="w-full pl-4 pr-12 py-3 rounded-xl bg-gray-50 border border-gray-200 text-xs sm:text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:bg-white focus:border-purple-600 focus:ring-2 focus:ring-purple-100 transition-all"
          />

          <button
            type="submit"
            disabled={!followUpInput.trim() || isSubmittingFollowUp}
            className={`absolute right-1.5 p-2 rounded-lg transition-all cursor-pointer ${
              followUpInput.trim() && !isSubmittingFollowUp
                ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-xs'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
            aria-label="질문 전송"
          >
            {isSubmittingFollowUp ? (
              <Sparkles className="w-4 h-4 animate-spin text-white" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
      </div>

    </div>
  );
}
