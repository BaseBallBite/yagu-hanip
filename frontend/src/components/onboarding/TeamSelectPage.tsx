
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Sparkles,
  Check,
  HelpCircle,
  Megaphone,
  Heart,
  Compass,
} from 'lucide-react';
import { OnboardingLayout } from './OnboardingLayout';

export interface TeamSelectPageProps {
  onNavigate: (path: string) => void;
}

interface TeamData {
  id: string;
  name: string;
  fullName: string;
  initial: string;
  primaryColor: string;
  lightBg: string;
  hoverBorder: string;
  textColor: string;
  stadium: string;
}

// KBO 10개 구단 - 서로 구분하기 쉬운 UI 색상
const KBO_TEAMS: TeamData[] = [
{
  id: 'kia',
  name: 'KIA',
  fullName: '타이거즈',
  initial: 'KIA',
primaryColor: '#D71920',
lightBg: '#FFF1F2',
hoverBorder: '#FCA5A5',
  textColor: '#FFFFFF',
  stadium: '광주-기아 챔피언스필드',
},
  {
    id: 'samsung',
    name: '삼성',
    fullName: '라이온즈',
    initial: '삼성',
    primaryColor: '#0066B3',
    lightBg: '#EFF6FF',
    hoverBorder: '#60A5FA',
    textColor: '#FFFFFF',
    stadium: '대구 라이온즈파크',
  },
{
  id: 'lg',
  name: 'LG',
  fullName: '트윈스',
  initial: 'LG',
primaryColor: '#D41470',
lightBg: '#FFF0F7',
hoverBorder: '#F9A8D4',
  textColor: '#FFFFFF',
  stadium: '서울 잠실야구장',
},
  {
    id: 'doosan',
    name: '두산',
    fullName: '베어스',
    initial: '두산',
    primaryColor: '#171735',
    lightBg: '#F1F5F9',
    hoverBorder: '#8183A6',
    textColor: '#FFFFFF',
    stadium: '서울 잠실야구장',
  },
  {
    id: 'kt',
    name: 'KT',
    fullName: '위즈',
    initial: 'KT',
    primaryColor: '#333333',
    lightBg: '#F5F5F5',
    hoverBorder: '#9CA3AF',
    textColor: '#FFFFFF',
    stadium: '수원 KT위즈파크',
  },
{
  id: 'ssg',
  name: 'SSG',
  fullName: '랜더스',
  initial: 'SSG',
primaryColor: '#F04E5E',
lightBg: '#FFF1F3',
hoverBorder: '#FDA4AF',
  textColor: '#FFFFFF',
  stadium: '인천 SSG랜더스필드',
},
{
  id: 'lotte',
  name: '롯데',
  fullName: '자이언츠',
  initial: '롯데',
  primaryColor: '#285477',
  lightBg: '#EFF6FA',
  hoverBorder: '#7DD3FC',
  textColor: '#FFFFFF',
  stadium: '부산 사직야구장',
},
    {
    id: 'hanwha',
    name: '한화',
    fullName: '이글스',
    initial: '한화',
    primaryColor: '#FF6B00',
    lightBg: '#FFF4E8',
    hoverBorder: '#FFB067',
    textColor: '#FFFFFF',
    stadium: '대전 한화생명이글스파크',
  },
{
  id: 'nc',
  name: 'NC',
  fullName: '다이노스',
  initial: 'NC',
  primaryColor: '#C9A34E',
  lightBg: '#FFFBEB',
  hoverBorder: '#D6B76A',
  textColor: '#172033',
  stadium: '창원 NC파크',
},
  {
    id: 'kiwoom',
    name: '키움',
    fullName: '히어로즈',
    initial: '키움',
    primaryColor: '#760D35',
    lightBg: '#FFF1F5',
    hoverBorder: '#BE5678',
    textColor: '#FFFFFF',
    stadium: '서울 고척스카이돔',
  },
];

// 구단 로고 대신 사용하는 텍스트 배지
function TeamLogoRenderer({ team }: { team: TeamData }) {
  return (
    <div
      className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-2 font-black text-sm shadow-xs select-none transition-transform group-hover:scale-105 shrink-0"
      style={{
        backgroundColor: team.primaryColor,
        color: team.textColor,
      }}
      aria-label={`${team.name} 구단`}
    >
      <span>{team.initial}</span>
    </div>
  );
}

export function TeamSelectPage({
  onNavigate,
}: TeamSelectPageProps) {
  const [selectedTeam, setSelectedTeam] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('favoriteTeam') || '';
    }
    return '';
  });

  const [hoveredTeam, setHoveredTeam] = useState<string | null>(
    null
  );

  const handleSelectTeam = (teamName: string) => {
    setSelectedTeam(teamName);

    if (typeof window !== 'undefined') {
      localStorage.setItem('favoriteTeam', teamName);
    }
  };

  const handleSelectNone = () => {
    setSelectedTeam('NONE');

    if (typeof window !== 'undefined') {
      localStorage.setItem('favoriteTeam', 'NONE');
    }
  };

  const handleSkip = () => {
    onNavigate('/game');
  };

  const handlePrev = () => {
    onNavigate('/onboarding/2');
  };

  const handleNext = () => {
    if (selectedTeam && typeof window !== 'undefined') {
      localStorage.setItem('favoriteTeam', selectedTeam);
    }

    onNavigate('/game');
  };

  const getCheerMessage = (teamName: string) => {
    if (teamName === 'NONE') {
      return '모든 구단의 경기와 하이라이트를 골고루 보여드릴게요 ⚾';
    }

    const hasBatchim = ['삼성', '두산', '키움'].includes(
      teamName
    );
    const particle = hasBatchim ? '을' : '를';

    return `${teamName}${particle} 응원할게요 ⚾`;
  };

  const isNoneSelected = selectedTeam === 'NONE';

  return (
    <OnboardingLayout
      currentStep={3}
      totalSteps={3}
      onSkip={handleSkip}
      onPrev={handlePrev}
      onNext={handleNext}
      prevButtonLabel="이전"
      nextButtonLabel="시작하기"
      leftColClass="lg:col-span-5"
      rightColClass="lg:col-span-7"
      leftContent={
        <div className="flex flex-col items-start text-left w-full">
          {/* 작은 라벨 */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/90 text-purple-700 text-xs font-bold mb-4">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>마지막 설정</span>
          </div>

          {/* 제목 */}
          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight mb-4 leading-snug">
            나의 팀을 골라 주세요
          </h1>

          {/* 설명 */}
          <p className="text-base sm:text-lg text-gray-600 leading-relaxed font-normal mb-8 whitespace-pre-line">
            응원하는 팀을 고르면{"\n"}
            해당 팀의{' '}
            <span className="font-semibold text-gray-900">
              경기와 하이라이트
            </span>
            를 먼저 보여드려요.{"\n\n"}
            상단 설정 메뉴에서{' '}
            <span className="text-purple-700 font-semibold">
              언제든 변경
            </span>
            할 수 있어요.
          </p>

          {/* 맞춤형 야구 브리핑 안내 */}
          <div className="w-full bg-white rounded-2xl p-5 border border-purple-100 shadow-sm mb-6 relative overflow-hidden">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-purple-100/80 text-purple-700 flex items-center justify-center shrink-0 shadow-xs">
                <Megaphone className="w-7 h-7 text-purple-600" />
              </div>

              <div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-purple-700 mb-0.5">
                  <Heart className="w-3.5 h-3.5 fill-purple-500 text-purple-500" />
                  <span>맞춤형 야구 브리핑</span>
                </div>

                <p className="text-xs sm:text-sm text-gray-600 font-medium">
                  선택한 팀의 오늘 경기 점수와 핵심 명장면을 가장 빠르게 확인할 수 있어요.
                </p>
              </div>
            </div>
          </div>

          {/* 하단 안내 */}
          <div className="w-full p-4 rounded-2xl bg-gray-50 border border-gray-200/80 text-gray-700 flex items-start gap-3">
            <HelpCircle className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />

            <p className="text-xs sm:text-sm font-medium leading-relaxed text-gray-600">
              팀을 아직 정하지 못했다면{"\n"}
              <span className="font-semibold text-gray-800">
                나중에 선택해도 괜찮아요!
              </span>
            </p>
          </div>
        </div>
      }
      rightContent={
        <div className="w-full flex flex-col">
          {/* 응원팀 선택 헤더 */}
          <div className="flex items-center justify-between mb-3.5">
            <div className="text-sm font-bold text-gray-800 flex items-center gap-1.5">
              <span>응원 팀 선택</span>
              <span className="text-xs font-medium text-gray-400">
                · 하나를 선택하세요
              </span>
            </div>

            {selectedTeam && (
              <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100">
                선택됨:{' '}
                {selectedTeam === 'NONE'
                  ? '응원 팀 없음'
                  : selectedTeam}
              </span>
            )}
          </div>

          {/* 응원팀 없음 카드 */}
          <button
            type="button"
            onClick={handleSelectNone}
            className={`w-full p-4 mb-4 rounded-2xl border transition-all duration-200 text-left flex items-center justify-between cursor-pointer group relative overflow-hidden ${
              isNoneSelected
                ? 'bg-purple-50/80 border-2 border-purple-600 ring-2 ring-purple-300/40 shadow-sm'
                : 'bg-white border-gray-200/90 hover:border-purple-300 hover:shadow-xs'
            }`}
          >
            <div
              className={`absolute top-0 left-0 right-0 h-[2.5px] transition-colors ${
                isNoneSelected
                  ? 'bg-purple-600'
                  : 'bg-transparent group-hover:bg-purple-200'
              }`}
            />

            <div className="flex items-center gap-3.5">
              <div
                className={`w-11 h-11 rounded-xl flex items-center justify-center transition-colors ${
                  isNoneSelected
                    ? 'bg-purple-600 text-white shadow-xs'
                    : 'bg-gray-100 text-gray-500 group-hover:bg-purple-100 group-hover:text-purple-600'
                }`}
              >
                <Compass className="w-5 h-5" />
              </div>

              <div>
                <div className="text-sm sm:text-base font-extrabold text-gray-900 group-hover:text-purple-800 transition-colors">
                  아직 응원하는 팀이 없어요
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  팀을 정하지 않아도 서비스를 이용할 수 있어요.
                </div>
              </div>
            </div>

            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${
                isNoneSelected
                  ? 'bg-purple-600 text-white shadow-xs scale-100'
                  : 'border-2 border-gray-300 text-transparent group-hover:border-purple-300'
              }`}
            >
              <Check className="w-3.5 h-3.5 stroke-[3]" />
            </div>
          </button>

          {/* KBO 10개 구단 */}
          <div className="text-xs font-bold text-gray-400 mb-2.5 uppercase tracking-wider flex items-center gap-1.5">
            <span>KBO 10개 구단</span>
          </div>

          {/* 구단 선택 카드 */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {KBO_TEAMS.map((team) => {
              const isSelected = selectedTeam === team.name;
              const isHovered = hoveredTeam === team.id;

              return (
                <button
                  key={team.id}
                  type="button"
                  onClick={() => handleSelectTeam(team.name)}
                  onMouseEnter={() => setHoveredTeam(team.id)}
                  onMouseLeave={() => setHoveredTeam(null)}
                  style={{
                    backgroundColor: isSelected
                      ? team.lightBg
                      : '#FFFFFF',
                    borderColor: isSelected
                      ? team.primaryColor
                      : isHovered
                      ? team.hoverBorder
                      : 'rgba(229, 231, 235, 0.9)',
                  }}
                  className={`relative p-3.5 sm:p-4 rounded-2xl transition-all duration-200 text-center flex flex-col items-center justify-center cursor-pointer group border overflow-hidden ${
                    isSelected
                      ? 'border-2 shadow-md -translate-y-1 scale-[1.01]'
                      : 'hover:shadow-md hover:-translate-y-1 shadow-xs'
                  }`}
                  aria-pressed={isSelected}
                  title={`${team.name} ${team.fullName} (${team.stadium})`}
                >
                  {/* 카드 상단 구단 색상 라인 */}
                  <div
                    className="absolute top-0 left-2 right-2 h-[3px] rounded-full transition-opacity"
                    style={{
                      backgroundColor: team.primaryColor,
                      opacity: isSelected
                        ? 1
                        : isHovered
                        ? 0.7
                        : 0.35,
                    }}
                  />

                  {/* 선택된 구단 체크 표시 */}
                  {isSelected && (
                    <div
                      className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full text-white flex items-center justify-center shadow-xs animate-in zoom-in-75 duration-200"
                      style={{
                        backgroundColor: team.primaryColor,
                      }}
                    >
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    </div>
                  )}

                  {/* 구단명 색상 배지 */}
                  <div className="mt-1">
                    <TeamLogoRenderer team={team} />
                  </div>

                  {/* 구단명 */}
                  <span className="text-sm sm:text-base font-extrabold tracking-tight text-gray-900 leading-tight">
                    {team.name}
                  </span>

                  {/* 전체 구단명 */}
                  <span className="text-[11px] text-gray-500 font-medium mt-0.5">
                    {team.fullName}
                  </span>
                </button>
              );
            })}
          </div>

          {/* 선택 결과 안내 */}
          <div className="mt-5 min-h-[46px] flex items-center justify-center">
            {selectedTeam ? (
              <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-purple-50 border border-purple-200 text-purple-900 text-sm font-bold shadow-xs animate-in fade-in slide-in-from-bottom-2 duration-300">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span>{getCheerMessage(selectedTeam)}</span>
              </div>
            ) : (
              <div className="text-xs text-gray-400 font-medium">
                구단 카드를 클릭하거나 "아직 응원하는 팀이 없어요"를 선택해보세요.
              </div>
            )}
          </div>
        </div>
      }
    />
  );
}
