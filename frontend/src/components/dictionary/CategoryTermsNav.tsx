/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { DICTIONARY_CATEGORIES, DictionaryCategory } from '../../data/mockDictionaryData';
import { Layers, Bookmark, Check } from 'lucide-react';

interface CategoryTermsNavProps {
  selectedTermName: string;
  onSelectTerm: (term: string) => void;
}

export function CategoryTermsNav({
  selectedTermName,
  onSelectTerm,
}: CategoryTermsNavProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-5 sm:p-6 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col gap-6">
      
      {/* Card Top Title */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
            <Bookmark className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-black text-gray-900 tracking-tight">
              용어 탐색
            </h2>
            <p className="text-xs text-gray-400">
              카테고리별 핵심 야구 용어
            </p>
          </div>
        </div>

        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-100">
          31개 주요 용어
        </span>
      </div>

      {/* 3 Categories Stack */}
      <div className="space-y-6">
        {DICTIONARY_CATEGORIES.map((cat: DictionaryCategory) => (
          <div key={cat.id}>
            {/* Category Header */}
            <div className="flex items-center gap-1.5 mb-3">
              <span className="w-1.5 h-3.5 bg-purple-600 rounded-full" />
              <h3 className="text-xs sm:text-sm font-extrabold text-gray-700">
                {cat.name}
              </h3>
              <span className="text-[11px] text-gray-400 font-medium">
                ({cat.terms.length})
              </span>
            </div>

            {/* Chips Grid */}
            <div className="flex flex-wrap gap-2">
              {cat.terms.map((term: string) => {
                const isSelected = selectedTermName === term;

                return (
                  <button
                    key={term}
                    type="button"
                    onClick={() => onSelectTerm(term)}
                    className={`px-3 py-1.5 rounded-xl text-xs sm:text-[13px] font-bold transition-all duration-150 cursor-pointer flex items-center gap-1.5 group ${
                      isSelected
                        ? 'bg-purple-600 text-white shadow-md shadow-purple-600/25 ring-2 ring-purple-300 scale-[1.02]'
                        : 'bg-gray-50/80 hover:bg-purple-50 text-gray-700 hover:text-purple-700 border border-gray-200/80 hover:border-purple-300 hover:shadow-xs'
                    }`}
                  >
                    <span>{term}</span>
                    {isSelected && (
                      <Check className="w-3.5 h-3.5 stroke-[3] text-white" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
