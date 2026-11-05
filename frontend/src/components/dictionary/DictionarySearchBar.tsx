/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Search, X, Sparkles } from 'lucide-react';

interface DictionarySearchBarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSearchSubmit: (query: string) => void;
}

export function DictionarySearchBar({
  searchQuery,
  onSearchChange,
  onSearchSubmit,
}: DictionarySearchBarProps) {
  const [localInput, setLocalInput] = useState<string>(searchQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearchSubmit(localInput.trim());
  };

  const handleClear = () => {
    setLocalInput('');
    onSearchChange('');
    onSearchSubmit('');
  };

  return (
    <form onSubmit={handleSubmit} className="w-full relative">
      <div className="relative flex items-center w-full">
        {/* Search Icon */}
        <div className="absolute left-4 sm:left-5 text-gray-400 pointer-events-none flex items-center">
          <Search className="w-5 h-5 text-purple-600" />
        </div>

        {/* Input Field */}
        <input
          type="text"
          value={localInput}
          onChange={(e) => {
            setLocalInput(e.target.value);
            onSearchChange(e.target.value);
          }}
          placeholder="궁금한 야구 용어를 검색해보세요. 예: 병살, 도루, 낫아웃"
          className="w-full pl-12 sm:pl-13 pr-28 sm:pr-32 py-4 rounded-2xl bg-white border border-gray-200/90 shadow-md shadow-purple-950/5 text-sm sm:text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-100 transition-all"
        />

        {/* Clear Button */}
        {localInput && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-24 sm:right-28 text-gray-400 hover:text-gray-600 p-1.5 rounded-full hover:bg-gray-100 transition cursor-pointer"
            aria-label="검색어 지우기"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        {/* Search Submit Button */}
        <button
          type="submit"
          className="absolute right-2 sm:right-2.5 px-4 sm:px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white font-bold text-xs sm:text-sm transition-all duration-200 shadow-sm shadow-purple-600/25 flex items-center gap-1.5 cursor-pointer hover:scale-[1.02]"
        >
          <span>검색</span>
        </button>
      </div>
    </form>
  );
}
