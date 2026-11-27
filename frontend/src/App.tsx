
import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Zap,
  Info,
} from 'lucide-react';

import { OnboardingStep1 } from './components/onboarding/OnboardingStep1';
import { OnboardingStep2 } from './components/onboarding/OnboardingStep2';
import { TeamSelectPage } from './components/onboarding/TeamSelectPage';
import { GameDashboard } from './components/game/GameDashboard';
import { HighlightsPage } from './components/highlights/HighlightsPage';
import { RankingPage } from './components/ranking/RankingPage';
import { DictionaryPage } from './components/dictionary/DictionaryPage';
import { MyPage } from './components/my/MyPage';
import { TeamMascot } from './components/common/TeamMascot';


const KNOWN_PATHS = [
  '/guide',
  '/onboarding',
  '/onboarding/2',
  '/team-select',
  '/game',
  '/highlights',
  '/ranking',
  '/dictionary',
  '/my',
];

export default function App() {
  const [currentPath, setCurrentPath] = useState<string>(() => {
    const path = window.location.pathname;
    if (KNOWN_PATHS.includes(path)) return path;

    return localStorage.getItem('yagu_onboarding_completed') === 'true'
      ? '/game'
      : '/';
  });

  const [onboardingCompleted, setOnboardingCompleted] =
    useState<boolean>(
      () => localStorage.getItem('yagu_onboarding_completed') === 'true'
    );

  const [isWhyActive, setIsWhyActive] = useState<boolean>(false);

  const [isGuideReplay, setIsGuideReplay] = useState<boolean>(
    () => window.location.pathname === '/guide'
  );

  // 선택한 응원팀에 따라 전체 UI 테마 적용
  useEffect(() => {
    const applyTeamTheme = () => {
      const favoriteTeam = localStorage.getItem('favoriteTeam');

      const teamMap: Record<string, string> = {
        KIA: 'kia',
        삼성: 'samsung',
        LG: 'lg',
        두산: 'doosan',
        KT: 'kt',
        SSG: 'ssg',
        롯데: 'lotte',
        한화: 'hanwha',
        NC: 'nc',
        키움: 'kiwoom',
      };

      const teamId = favoriteTeam
        ? teamMap[favoriteTeam] ?? 'none'
        : 'none';

      if (teamId === 'none') {
        document.documentElement.removeAttribute('data-team');
      } else {
        document.documentElement.setAttribute('data-team', teamId);
      }
    };

    applyTeamTheme();
    window.addEventListener('storage', applyTeamTheme);
    window.addEventListener('yagu:favorite-team-changed', applyTeamTheme);

    return () => {
      window.removeEventListener('storage', applyTeamTheme);
      window.removeEventListener('yagu:favorite-team-changed', applyTeamTheme);
    };
  }, [currentPath]);

  // 페이지 이동
  const navigate = (path: string) => {
    let nextPath = path;

    // MY에서 이용 가이드 다시 보기
    if (nextPath === '/guide') {
      setIsGuideReplay(true);
    }

    // 가이드 다시 보기 중에는 랜딩으로 이동
    if (nextPath === '/' && isGuideReplay) {
      nextPath = '/guide';
    } else if (
      nextPath === '/' &&
      localStorage.getItem('yagu_onboarding_completed') === 'true'
    ) {
      nextPath = '/game';
    }

    const isOnboardingPage = [
      '/onboarding',
      '/onboarding/2',
      '/team-select',
    ].includes(currentPath);

    // 온보딩을 마치면 완료 상태 저장
    if (isOnboardingPage && nextPath === '/game') {
      localStorage.setItem('yagu_onboarding_completed', 'true');
      setOnboardingCompleted(true);
    }

    // 경기 화면 진입 시 가이드 다시 보기 종료
    if (nextPath === '/game') {
      setIsGuideReplay(false);
    }

    setCurrentPath(nextPath);
    window.history.pushState({}, '', nextPath);

    window.scrollTo({
      top: 0,
      behavior: 'auto',
    });
  };

  const handleStart = () => {
    navigate(
      isGuideReplay || !onboardingCompleted
        ? '/onboarding'
        : '/game'
    );
  };

  // 브라우저 뒤로가기 / 앞으로가기
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname || '/';
      setCurrentPath(path);
      setIsGuideReplay(path === '/guide');
    };

    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  const handleWhyClick = () => {
    setIsWhyActive((prev) => !prev);
  };

  // 상단 메뉴
  const navItems = [
    { label: '경기', path: '/game' },
    { label: '하이라이트', path: '/highlights' },
    { label: '순위', path: '/ranking' },
    { label: '야구사전', path: '/dictionary' },
    { label: 'MY', path: '/my' },
  ];

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#1E232A] flex flex-col selection:bg-purple-100 selection:text-purple-900">

      {/* =========================
          COMMON HEADER
      ========================== */}
      <header className="sticky top-0 z-30 w-full shrink-0 bg-white/95 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-[1350px] mx-auto px-4 sm:px-6 h-[72px] flex items-center justify-between gap-4">

          {/* Logo / Service Name */}
          <button
            type="button"
            onClick={() => navigate('/')}
            className="flex items-center gap-3 text-left group cursor-pointer focus:outline-none"
            aria-label="야구한입 홈으로 이동"
          >
            <div className="w-10 h-10 rounded-2xl overflow-hidden transition-transform group-hover:scale-105 shrink-0">
              <TeamMascot variant="header" alt="야구한입 로고" className="w-full h-full object-cover" />
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-black text-gray-900 tracking-tight group-hover:text-purple-700 transition-colors">
                야구한입
              </span>

              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-100">
                AI 입문 해설
              </span>
            </div>
          </button>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-3 lg:gap-5 text-sm font-medium">
            {navItems.map((item) => (
              <button
                key={item.path}
                type="button"
                onClick={() => navigate(item.path)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border transition-colors cursor-pointer font-bold whitespace-nowrap ${
                  currentPath === item.path
                    ? 'text-purple-600 bg-purple-50 border-purple-200/80 shadow-xs'
                    : 'text-gray-600 border-transparent hover:text-purple-600 hover:bg-purple-50/60'
                }`}
              >
                <span>{item.label}</span>

                <span
                  aria-hidden="true"
                  className={`w-1.5 h-1.5 shrink-0 rounded-full ${currentPath === item.path ? 'bg-purple-600' : 'bg-transparent'}`}
                />
              </button>
            ))}
          </nav>

          {/* Header CTA */}
          <div className="flex items-center gap-3">
            {currentPath === '/' || currentPath === '/guide' ? (
              <button
                type="button"
                onClick={handleStart}
                className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-sm transition-all duration-200 shadow-sm shadow-purple-600/20 hover:shadow hover:shadow-purple-600/30 active:scale-95 cursor-pointer"
              >
                시작하기
              </button>
            ) : null}
          </div>
        </div>
      </header>

      {/* =========================
          PAGE ROUTING
      ========================== */}

      {currentPath === '/onboarding' ? (
        <main className="flex-1 flex flex-col justify-center">
          <OnboardingStep1 onNavigate={navigate} />
        </main>
      ) : currentPath === '/onboarding/2' ? (
        <main className="flex-1 flex flex-col justify-center">
          <OnboardingStep2 onNavigate={navigate} />
        </main>
      ) : currentPath === '/team-select' ? (
        <main className="flex-1 flex flex-col justify-center">
          <TeamSelectPage onNavigate={navigate} />
        </main>
      ) : currentPath === '/game' ? (
        <main className="flex-1 flex flex-col justify-center">
          <GameDashboard onNavigate={navigate} />
        </main>
      ) : currentPath === '/highlights' ? (
        <main className="flex-1 flex flex-col justify-center">
          <HighlightsPage onNavigate={navigate} />
        </main>
      ) : currentPath === '/ranking' ? (
        <main className="flex-1 flex flex-col justify-center">
          <RankingPage onNavigate={navigate} />
        </main>
      ) : currentPath === '/dictionary' ? (
        <main className="flex-1 flex flex-col justify-center">
          <DictionaryPage />
        </main>
      ) : currentPath === '/my' ? (
        <main className="flex-1 flex flex-col justify-center">
          <MyPage onNavigate={navigate} />
        </main>
      ) : (

        /* =========================
            LANDING PAGE
        ========================== */
        <main className="flex-1 flex flex-col justify-center py-10 lg:py-16">
          <div className="max-w-[1200px] w-full mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-center">

              {/* LEFT */}
              <div className="lg:col-span-7 xl:col-span-7 flex flex-col items-start text-left">

                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-50 border border-purple-100 text-purple-700 text-xs sm:text-sm font-semibold mb-6 shadow-xs">
                  <Sparkles className="w-4 h-4 text-purple-600 animate-pulse" />
                  <span>야구 초보자를 위한 1초 맞춤 해설</span>
                </div>

                {/* Title */}
                <h1 className="text-4xl sm:text-5xl font-black text-purple-600 tracking-tight mb-4">
                  야구한입
                </h1>

                {/* Main Copy */}
                <h2 className="text-2xl sm:text-3xl lg:text-[30px] xl:text-[32px] font-extrabold text-gray-900 leading-[1.38] tracking-tight mb-5 whitespace-pre-line">
                  야구를 하나도 몰라도,{"\n"}

                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-purple-100/80 text-purple-900 mx-1 align-middle">
                    <TeamMascot alt="" className="inline-block h-[1em] w-[1em] shrink-0 object-contain" />
                    <span>한입만!</span>
                  </span>{' '}

                  한 번으로 방금 장면을 <span className="whitespace-nowrap">이해해요</span>
                </h2>

                {/* Description */}
                <p className="text-base lg:text-[15px] xl:text-base text-gray-600 leading-relaxed font-normal mb-8 max-w-none lg:whitespace-nowrap">
                  경기를 보다 이해하기 어려운 장면을 만나면,{" "}
                  <span className="font-semibold text-gray-800">
                    AI가 쉽고 빠르게 설명
                  </span>
                  해줘요.
                </p>

                {/* Feature List */}
                <div className="w-full space-y-3 mb-9">

                  {/* Feature 1 */}
                  <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm hover:border-purple-200 hover:shadow-md transition-all duration-200 flex items-start gap-4">
                    <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 font-bold flex items-center justify-center shrink-0 text-sm mt-0.5">
                      1
                    </div>

                    <div>
                      <h3 className="font-bold text-gray-900 text-[15px] sm:text-base flex items-center gap-1.5 flex-wrap">
                        <span>경기 중</span>

                        <span className="inline-flex items-center gap-1 text-purple-600 font-black">
                          <TeamMascot alt="" className="h-5 w-5 shrink-0 object-contain" />
                          한입만!
                        </span>

                        <span>버튼을 누르면 방금 플레이를 쉽게 설명</span>
                      </h3>

                      <p className="text-xs sm:text-sm text-gray-500 mt-0.5">
                        복잡한 규칙과 판정도 일상 언어로 3줄 안에 알기 쉽게
                        요약해 드려요.
                      </p>
                    </div>
                  </div>

                  {/* Feature 2 */}
                  <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm hover:border-purple-200 hover:shadow-md transition-all duration-200 flex items-start gap-4">
                    <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 font-bold flex items-center justify-center shrink-0 text-sm mt-0.5">
                      2
                    </div>

                    <div>
                      <h3 className="font-bold text-gray-900 text-[15px] sm:text-base">
                        어려운 야구 용어는 야구사전에서 확인
                      </h3>

                      <p className="text-xs sm:text-sm text-gray-500 mt-0.5">
                        인필드플라이, 보크, 슬라이더 등 낯선 단어를 터치
                        한 번으로 확인해요.
                      </p>
                    </div>
                  </div>

                  {/* Feature 3 */}
                  <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm hover:border-purple-200 hover:shadow-md transition-all duration-200 flex items-start gap-4">
                    <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 font-bold flex items-center justify-center shrink-0 text-sm mt-0.5">
                      3
                    </div>

                    <div>
                      <h3 className="font-bold text-gray-900 text-[15px] sm:text-base">
                        실제 경기 기록을 기반으로 상황과 맥락을 설명
                      </h3>

                      <p className="text-xs sm:text-sm text-gray-500 mt-0.5">
                        투수의 구종, 볼카운트, 주자 위치를 반영해
                        지금 중요한 순간인 이유를 알려줘요.
                      </p>
                    </div>
                  </div>
                </div>

                {/* CTA */}
                <div className="w-full sm:w-auto flex flex-col sm:flex-row items-center gap-4">
                  <button
                    type="button"
                    onClick={handleStart}
                    className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white font-bold text-lg shadow-lg shadow-purple-600/25 hover:shadow-xl hover:shadow-purple-600/35 hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-3 group cursor-pointer"
                  >
                    <span>시작하기</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>

                  <div className="text-xs text-gray-500 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-purple-600" />
                    <span>설치 없이 웹에서 바로 시작</span>
                  </div>
                </div>
              </div>

              {/* RIGHT */}
              <div className="lg:col-span-5 xl:col-span-5">
                <div className="relative group">

                  {/* Backdrop */}
                  <div className="absolute -inset-1 bg-gradient-to-r from-purple-200/50 via-purple-100/40 to-pink-100/40 rounded-3xl blur-xl opacity-70 group-hover:opacity-100 transition duration-500" />

                  {/* Preview Card */}
                  <div className="relative bg-white rounded-3xl p-6 sm:p-8 border border-gray-100 shadow-xl shadow-gray-200/60 hover:shadow-2xl hover:shadow-purple-900/10 transition-all duration-300">

                    {/* Card Header */}
                    <div className="flex items-center justify-between pb-5 border-b border-gray-100">
                      <div className="flex items-center gap-2">
                        <span className="relative flex h-2.5 w-2.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
                        </span>

                        <span className="text-xs font-bold text-red-600 tracking-wider">
                          경기 화면 미리보기
                        </span>
                      </div>

                      <div className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-700">
                        시연용 가상 상황
                      </div>
                    </div>

                    {/* Scoreboard */}
                    <div className="mt-5 bg-gradient-to-br from-gray-50 to-purple-50/30 rounded-2xl p-4 sm:p-5 border border-gray-100">
                      <div className="flex items-center justify-between">

                        {/* KT */}
                        <div className="flex items-center gap-3">
                          <div className="w-11 h-11 rounded-2xl bg-black text-white font-black text-sm flex items-center justify-center shadow-xs">
                            KT
                          </div>

                          <div>
                            <div className="text-xs font-medium text-gray-500">
                              홈
                            </div>
                            <div className="text-lg font-black text-gray-900">
                              KT
                            </div>
                          </div>
                        </div>

                        {/* Score */}
                        <div className="text-center px-4">
                          <div className="text-2xl sm:text-3xl font-black tracking-wider text-gray-900 flex items-center gap-3">
                            <span className="text-purple-600">3</span>
                            <span className="text-gray-300 font-light">:</span>
                            <span className="text-gray-800">2</span>
                          </div>

                          <div className="mt-1 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs font-bold">
                            <span>9회초</span>
                            <span>·</span>
                            <span>투구 전 · 0아웃</span>
                          </div>
                        </div>

                        {/* KIA */}
                        <div className="flex items-center gap-3 flex-row-reverse text-right">
                          <div className="w-11 h-11 rounded-2xl bg-[#EA0029] text-white font-black text-sm flex items-center justify-center shadow-xs">
                            KIA
                          </div>

                          <div>
                            <div className="text-xs font-medium text-gray-500">
                              원정
                            </div>
                            <div className="text-lg font-black text-gray-900">
                              KIA
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Runner / Count */}
                      <div className="mt-3 pt-3 border-t border-gray-200/60 flex items-center justify-between text-xs text-gray-600">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-400">
                            주자
                          </span>

                          <div className="flex items-center gap-1">
                            <span
                              className="w-2.5 h-2.5 border border-gray-300 rounded-[2px] rotate-45 inline-block bg-white"
                              title="3루"
                            />
                            <span
                              className="w-2.5 h-2.5 border border-gray-300 rounded-[2px] rotate-45 inline-block bg-white"
                              title="2루"
                            />
                            <span
                              className="w-2.5 h-2.5 border border-purple-500 rounded-[2px] rotate-45 inline-block bg-purple-500"
                              title="1루 주자 있음"
                            />
                          </div>

                          <span className="text-[11px] text-purple-700 font-semibold ml-1">
                            1루에 주자 있음
                          </span>
                        </div>

                        <div className="flex items-center gap-2 font-mono">
                          <span className="text-[11px]">
                            B{' '}
                            <span className="text-emerald-600 font-bold">2</span>
                          </span>

                          <span className="text-[11px]">
                            S{' '}
                            <span className="text-amber-500 font-bold">2</span>
                          </span>

                          <span className="text-[11px]">
                            O{' '}
                            <span className="text-red-500 font-bold">0</span>
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Current At Bat */}
                    <div className="mt-5 p-4 rounded-2xl bg-white border border-gray-100 shadow-xs">
                      <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5 flex items-center justify-between">
                        <span>현재 타석</span>

                        <span className="text-purple-600 font-medium text-[11px]">
                          2볼 2스트라이크
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="text-base sm:text-lg font-bold text-gray-900">
                          황대인{' '}
                          <span className="text-xs font-normal text-gray-500">
                            (KIA 타자)
                          </span>
                        </div>

                        <span className="text-xs font-black px-2 py-0.5 rounded bg-gray-100 text-gray-500">
                          VS
                        </span>

                        <div className="text-base sm:text-lg font-bold text-gray-900 text-right">
                          박영현{' '}
                          <span className="text-xs font-normal text-gray-500">
                            (KT 투수)
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Pitch Information */}
                    <div className="mt-4 p-4 rounded-2xl bg-purple-50/50 border border-purple-100">
                      <div className="flex items-center justify-between text-xs text-purple-700 font-semibold mb-2">
                        <span className="flex items-center gap-1.5">
                          <Zap className="w-3.5 h-3.5 text-purple-600" />
                          투구 정보
                        </span>

                        <span className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded text-[11px] font-bold">
                          스트라이크 존 하단
                        </span>
                      </div>

                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div>
                          <div className="text-sm sm:text-base font-extrabold text-gray-900 flex items-center gap-2">
                            <span>6구 슬라이더</span>

                            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white text-gray-600 border border-gray-200">
                              136km/h
                            </span>
                          </div>

                          <div className="text-xs sm:text-sm text-gray-600 font-medium mt-0.5">
                            헛스윙 · 136km/h
                          </div>
                        </div>

                        <div className="inline-flex items-center gap-1 text-sm sm:text-base font-black text-purple-700 bg-white px-3 py-1.5 rounded-xl border border-purple-200 shadow-xs self-start sm:self-auto">
                          <span>→ 삼진 아웃 · 1아웃</span>
                        </div>
                      </div>
                    </div>

                    {/* 한입만! Button */}
                    <div className="mt-5 flex items-center justify-between gap-3">
                      <div className="text-xs font-medium text-gray-500 flex items-center gap-1">
                        <Info className="w-3.5 h-3.5 text-purple-500" />
                        <span>궁금한 순간 언제든 눌러보세요</span>
                      </div>

                      <button
                        type="button"
                        aria-expanded={isWhyActive}
                        aria-controls="landing-explanation"
                        onClick={handleWhyClick}
                        className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs sm:text-sm font-bold transition-all duration-200 cursor-pointer shadow-xs ${
                          isWhyActive
                            ? 'bg-purple-600 text-white shadow-purple-500/20 ring-2 ring-purple-300'
                            : 'bg-gray-100 hover:bg-purple-100 text-gray-700 hover:text-purple-700'
                        }`}
                        title="클릭하여 AI 해설 보기 또는 접기"
                      >
                        
                        <TeamMascot alt="" className="h-5 w-5 shrink-0 object-contain" />
                        <span>한입만!</span>

                        <span className="text-[11px] font-normal opacity-90">
                          {isWhyActive ? '설명 접기' : '해설 보기'}
                        </span>
                      </button>
                    </div>

                    {/* AI Explanation */}
                    {isWhyActive && (
                      <div id="landing-explanation" className="mt-3.5 p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-700 text-white shadow-lg shadow-purple-900/15 transition-all duration-300">
                        <div className="flex items-center justify-between mb-2.5">
                          <div className="flex items-center gap-1.5 text-xs font-bold text-purple-100">
                            <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                            <span>해설 예시</span>
                          </div>

                          <span className="text-[10px] text-purple-200 bg-white/10 px-2 py-0.5 rounded-full">
                            초보자 맞춤 요약
                          </span>
                        </div>

                        <p className="text-sm sm:text-[15px] font-medium leading-relaxed text-purple-50 whitespace-pre-line">
                          "슬라이더가 아래쪽으로 떨어지면서 타자의 배트가
                          헛돌았어요.{"\n"}
                          스트라이크가 3개가 되어 삼진 아웃입니다."
                        </p>

                        <div className="mt-3.5 pt-3 border-t border-white/15 flex flex-wrap items-center gap-1.5 text-[11px]">
                          <span className="text-purple-200 font-semibold mr-1">
                            핵심 용어:
                          </span>

                          <span className="px-2 py-0.5 rounded-md bg-white/15 hover:bg-white/25 transition cursor-default font-medium">
                            #슬라이더 (떨어지는 변화구)
                          </span>

                          <span className="px-2 py-0.5 rounded-md bg-white/15 hover:bg-white/25 transition cursor-default font-medium">
                            #헛스윙 (공을 맞추지 못함)
                          </span>

                          <span className="px-2 py-0.5 rounded-md bg-white/15 hover:bg-white/25 transition cursor-default font-medium">
                            #삼진 (스트라이크 3개)
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Note */}
                    <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-400">
                      <span>서비스 기능 설명을 위한 가상 경기 예시</span>

                      <span className="font-semibold text-purple-600">
                        야구한입 프리뷰
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* =========================
          FOOTER
      ========================== */}
      <footer className="border-t border-gray-200/70 bg-white py-8 mt-auto">
        <div className="max-w-[1200px] mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <span className="font-bold text-gray-800">
              야구한입
            </span>

            <span>·</span>

            <span>
              야구 초보자를 위한 AI 경기 해설 서비스
            </span>
          </div>

          <div className="flex items-center gap-4 text-gray-400">
            <span>© 2026 야구한입. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
