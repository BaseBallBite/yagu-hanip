/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  DICTIONARY_CATEGORIES, 
  MOCK_TERM_DETAILS, 
  getTermDetailOrDefault, 
  TermDetail 
} from '../../data/mockDictionaryData';
import { DictionarySearchBar } from './DictionarySearchBar';
import { CategoryTermsNav } from './CategoryTermsNav';
import { TermDetailPanel } from './TermDetailPanel';
import { Sparkles, HelpCircle, Bot, AlertCircle, BookOpen } from 'lucide-react';

export function DictionaryPage() {
  const [selectedTermName, setSelectedTermName] = useState<string>('병살');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchNotFoundTerm, setSearchNotFoundTerm] = useState<string | null>(null);

  // Current active term detail
  const currentTermDetail: TermDetail = getTermDetailOrDefault(selectedTermName);

  const handleSelectTerm = (term: string) => {
    setSearchNotFoundTerm(null);
    setSelectedTermName(term);
  };

  const handleSearchSubmit = (query: string) => {
    if (!query) {
      setSearchNotFoundTerm(null);
      return;
    }

    setIsSearching(true);

    setTimeout(() => {
      setIsSearching(false);
      // Clean query string
      const trimmed = query.trim().replace(/^#/, '');

      // Check for exact or partial matches in all categories
      const allTerms = DICTIONARY_CATEGORIES.flatMap((c) => c.terms);
      const exactMatch = allTerms.find(
        (t) => t.toLowerCase() === trimmed.toLowerCase() || t.replace(/\s+/g, '') === trimmed.replace(/\s+/g, '')
      );

      const partialMatch = allTerms.find(
        (t) => t.includes(trimmed) || trimmed.includes(t)
      );

      if (exactMatch) {
        setSelectedTermName(exactMatch);
        setSearchNotFoundTerm(null);
      } else if (partialMatch) {
        setSelectedTermName(partialMatch);
        setSearchNotFoundTerm(null);
      } else if (MOCK_TERM_DETAILS[trimmed]) {
        setSelectedTermName(trimmed);
        setSearchNotFoundTerm(null);
      } else {
        // Not found in predefined list
        setSearchNotFoundTerm(trimmed);
      }
    }, 350);
  };

  // User requests generative explanation for custom searched term
  const handleGenerateCustomExplanation = () => {
    if (searchNotFoundTerm) {
      setIsSearching(true);
      setTimeout(() => {
        setIsSearching(false);
        setSelectedTermName(searchNotFoundTerm);
        setSearchNotFoundTerm(null);
      }, 400);
    }
  };

  return (
    <div className="w-full flex-1 py-6 sm:py-8 animate-fade-in">
      <div className="max-w-[1350px] w-full mx-auto px-4 sm:px-6">
        
        {/* Top Header Section */}
        <div className="mb-8 text-center max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/90 text-purple-700 text-xs font-bold mb-2">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>RAG 기반 야구 용어 지식 백과</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight">
            야구사전
          </h1>
          <p className="text-sm sm:text-base text-gray-500 mt-1.5 mb-6">
            모르는 야구 용어와 규칙을 초보자 눈높이로 쉽게 확인해보세요.
          </p>

          {/* Large Search Bar */}
          <DictionarySearchBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSearchSubmit={handleSearchSubmit}
          />
        </div>

        {/* 2-Column Desktop Grid (Left ~40% col-span-5, Right ~60% col-span-7) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column: Category Terms Navigation Chips */}
          <div className="lg:col-span-5 w-full">
            <CategoryTermsNav
              selectedTermName={selectedTermName}
              onSelectTerm={handleSelectTerm}
            />
          </div>

          {/* Right Column: AI Explanation & Follow-Up Q&A Panel */}
          <div className="lg:col-span-7 w-full">
            {isSearching ? (
              <div className="w-full bg-white rounded-3xl p-16 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col items-center justify-center text-center animate-in fade-in">
                <div className="w-12 h-12 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center mb-4 animate-spin">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div className="text-base font-extrabold text-gray-900 mb-1">
                  AI 야구사전 검색 중...
                </div>
                <p className="text-xs text-gray-500 max-w-xs">
                  KBO 공식 규칙과 해설 데이터를 기반으로 최적의 용어 설명을 찾고 있어요.
                </p>
              </div>
            ) : searchNotFoundTerm ? (
              /* Search Not Found State */
              <div className="w-full bg-white rounded-3xl p-10 sm:p-12 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col items-center justify-center text-center animate-in fade-in">
                <div className="w-16 h-16 rounded-3xl bg-amber-50 text-amber-600 flex items-center justify-center mb-4 text-2xl border border-amber-100">
                  <AlertCircle className="w-8 h-8" />
                </div>
                
                <h3 className="text-xl font-black text-gray-900 mb-2">
                  정확히 일치하는 용어가 없어요.
                </h3>
                
                <p className="text-xs sm:text-sm text-gray-500 max-w-sm mb-6 leading-relaxed">
                  '<span className="font-bold text-gray-800">{searchNotFoundTerm}</span>'에 대한 사전 등록 표제어가 없습니다. 생성형 AI에게 즉시 초보자용 맞춤 해설을 요청하시겠어요?
                </p>

                <button
                  type="button"
                  onClick={handleGenerateCustomExplanation}
                  className="px-6 py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white font-bold text-sm shadow-lg shadow-purple-600/25 transition-all duration-200 cursor-pointer flex items-center gap-2 hover:scale-[1.02]"
                >
                  <Bot className="w-4 h-4" />
                  <span>AI에게 쉽게 설명해달라고 하기</span>
                </button>
              </div>
            ) : (
              /* Regular AI Term Detail Panel */
              <TermDetailPanel
                term={currentTermDetail}
                onSelectRelatedTerm={handleSelectTerm}
              />
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
