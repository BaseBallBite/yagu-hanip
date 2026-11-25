
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useMemo, useState } from 'react';

import {
  fetchGames,
  fetchGameScreen,
  makeGameSummary,
  toRecentGame,
} from '../../data/gameApi';

import type {
  GameRecord,
  GameScreenData,
} from '../../data/gameApi';

import { GameScoreHeader } from './GameScoreHeader';
import { RecentGamesBar } from './RecentGamesBar';
import { CurrentAtBatCard } from './CurrentAtBatCard';
import { InningPlaysHistory } from './InningPlaysHistory';

import {
  AlertCircle,
  LoaderCircle,
  RefreshCw,
  CalendarDays,
  Search,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

const GAMES_PER_PAGE = 12;

const TEAMS = [
  '전체 구단',
  'KIA',
  'LG',
  '삼성',
  '두산',
  'KT',
  'SSG',
  '롯데',
  '한화',
  'NC',
  '키움',
];

const TEAM_CODES: Record<string, string> = {
  KIA: 'KIA',
  LG: 'LG',
  삼성: '삼성',
  두산: '두산',
  KT: 'KT',
  SSG: 'SSG',
  롯데: '롯데',
  한화: '한화',
  NC: 'NC',
  키움: '키움',
};

// 실제 API에서 팀 이름을 여러 형식으로 반환하더라도
// 검색 결과가 빠지지 않도록 별칭을 통일
const TEAM_ALIASES: Record<string, string> = {
  KIA: 'KIA',
  기아: 'KIA',
  'KIA 타이거즈': 'KIA',
  LG: 'LG',
  'LG 트윈스': 'LG',
  삼성: '삼성',
  '삼성 라이온즈': '삼성',
  두산: '두산',
  '두산 베어스': '두산',
  KT: 'KT',
  kt: 'KT',
  'KT 위즈': 'KT',
  SSG: 'SSG',
  'SSG 랜더스': 'SSG',
  롯데: '롯데',
  '롯데 자이언츠': '롯데',
  한화: '한화',
  '한화 이글스': '한화',
  NC: 'NC',
  'NC 다이노스': 'NC',
  키움: '키움',
  '키움 히어로즈': '키움',
};

function normalizeTeam(value: string): string {
  return TEAM_ALIASES[value] || value;
}

export function GameDashboard({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const [games, setGames] = useState<GameRecord[]>([]);
  const [selectedGameId, setSelectedGameId] = useState('');

  const [gameData, setGameData] =
    useState<GameScreenData | null>(null);

  const [selectedAtBatId, setSelectedAtBatId] =
    useState('');

  // 초기 화면은 이미 검증한 개막일 경기 표시
  const [selectedDate, setSelectedDate] =
    useState('2026-03-28');

  const [selectedTeam, setSelectedTeam] =
    useState('전체 구단');

  const [page, setPage] = useState(1);
  const [filtersCollapsed, setFiltersCollapsed] = useState(false);

  const [isLoadingGames, setIsLoadingGames] =
    useState(true);

  const [isLoadingPlays, setIsLoadingPlays] =
    useState(false);

  const [listError, setListError] = useState('');
  const [gameError, setGameError] = useState('');
  const [aiNotice, setAiNotice] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  // 1. 전체 경기 목록 불러오기
  useEffect(() => {
    let active = true;

    async function loadGames() {
      setIsLoadingGames(true);
      setListError('');

      try {
        const result = await fetchGames();

        if (!active) return;

        setGames(result);
      } catch (err) {
        if (!active) return;

        setListError(
          err instanceof Error
            ? err.message
            : '경기 목록을 불러오지 못했어요.'
        );
      } finally {
        if (active) {
          setIsLoadingGames(false);
        }
      }
    }

    loadGames();

    return () => {
      active = false;
    };
  }, [reloadKey]);

  // 2. 날짜 + 구단 조건으로 경기 검색
  const filteredGames = useMemo(() => {
    return games.filter((game) => {
      const dateMatches =
        !selectedDate ||
        game.game_date === selectedDate;

      const teamMatches =
        selectedTeam === '전체 구단' ||
        normalizeTeam(game.home) === selectedTeam ||
        normalizeTeam(game.away) === selectedTeam;

      return dateMatches && teamMatches;
    });
  }, [games, selectedDate, selectedTeam]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredGames.length / GAMES_PER_PAGE)
  );

  const displayedGames = useMemo(() => {
    const start = (page - 1) * GAMES_PER_PAGE;

    return filteredGames
      .slice(start, start + GAMES_PER_PAGE)
      .map(toRecentGame);
  }, [filteredGames, page]);

  // 3. 필터 결과가 바뀌면 선택 경기 동기화
  useEffect(() => {
    if (isLoadingGames) return;

    const exists = filteredGames.some(
      (game) => game.game_id === selectedGameId
    );

    if (!exists) {
      setSelectedGameId(
        filteredGames[0]?.game_id || ''
      );
    }
  }, [
    filteredGames,
    selectedGameId,
    isLoadingGames,
  ]);

  // 4. 선택한 경기의 플레이 API 호출
  useEffect(() => {
    if (!selectedGameId) {
      setGameData(null);
      setSelectedAtBatId('');
      setGameError('');
      return;
    }

    let active = true;

    async function loadGame() {
      setIsLoadingPlays(true);
      setGameData(null);
      setSelectedAtBatId('');
      setGameError('');
      setAiNotice(false);

      try {
        const result = await fetchGameScreen(
          selectedGameId
        );

        if (!active) return;

        setGameData(result);

        if (result.atBats.length > 0) {
          // 결과가 없는 진행 중/불완전한 투구 기록은 해설 대상으로 자동 선택하지 않는다.
          // 실제 결과 플레이 ID가 있는 가장 최근 타석을 우선 선택한다.
          const lastAtBat =
            [...result.atBats].reverse().find((item) => item.resultPlayId) ??
            result.atBats[result.atBats.length - 1];

          setSelectedAtBatId(lastAtBat.id);
        } else {
          setGameError(
            '이 경기에서 표시할 타석 기록을 찾지 못했어요.'
          );
        }
      } catch (err) {
        if (!active) return;

        setGameError(
          err instanceof Error
            ? err.message
            : '경기 기록을 불러오지 못했어요.'
        );
      } finally {
        if (active) {
          setIsLoadingPlays(false);
        }
      }
    }

    loadGame();

    return () => {
      active = false;
    };
  }, [selectedGameId, reloadKey]);

  const atBats = useMemo(
    () => gameData?.atBats ?? [],
    [gameData]
  );

  const currentAtBatIndex = useMemo(
    () =>
      atBats.findIndex(
        (item) => item.id === selectedAtBatId
      ),
    [atBats, selectedAtBatId]
  );

  const currentAtBat =
    currentAtBatIndex >= 0
      ? atBats[currentAtBatIndex]
      : null;

  const summary = useMemo(() => {
    if (
      !gameData ||
      !currentAtBat ||
      gameData.game.game_id !== selectedGameId
    ) {
      return null;
    }

    return makeGameSummary(
      gameData.game,
      currentAtBat
    );
  }, [gameData, currentAtBat, selectedGameId]);

  const handleDateChange = (value: string) => {
    setSelectedDate(value);
    setPage(1);
  };

  const handleTeamChange = (value: string) => {
    setSelectedTeam(value);
    setPage(1);
  };

  const handleSelectGame = (gameId: string) => {
    setSelectedGameId(gameId);
    setFiltersCollapsed(true);
    setAiNotice(false);
  };

  const handleSelectAtBat = (atBatId: string) => {
    setSelectedAtBatId(atBatId);
    setAiNotice(false);
  };

  const handlePrevAtBat = () => {
    if (currentAtBatIndex > 0) {
      handleSelectAtBat(
        atBats[currentAtBatIndex - 1].id
      );
    }
  };

  const handleNextAtBat = () => {
    if (
      currentAtBatIndex >= 0 &&
      currentAtBatIndex < atBats.length - 1
    ) {
      handleSelectAtBat(
        atBats[currentAtBatIndex + 1].id
      );
    }
  };

  const handleRetry = () => {
    setReloadKey((previous) => previous + 1);
  };

  // 필터 변경 후 일시적으로 이전 경기의
  // 데이터가 나타나지 않도록 방지
  const gameMatchesFilter = filteredGames.some(
    (game) => game.game_id === selectedGameId
  );

  const canShowGame =
    !isLoadingGames &&
    !isLoadingPlays &&
    gameMatchesFilter &&
    summary !== null &&
    currentAtBat !== null &&
    gameData !== null;

  return (
    <div className="w-full flex-1 py-6 sm:py-8 animate-fade-in">
      <div className="max-w-[1450px] w-full mx-auto px-5 sm:px-8 lg:px-10">

        {/* 페이지 제목 */}
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-900">
              경기 기록
            </h1>

            <p className="mt-1 text-sm text-gray-500">
              실제 KBO 경기의 타석과 투구 기록을 확인해 보세요.
            </p>
          </div>

          <span className="text-xs font-bold text-purple-700 bg-purple-50 border border-purple-100 rounded-full px-3 py-1.5">
            2026 시즌
          </span>
        </div>

        {/* 데스크톱에서는 좌측 경기 선택 + 우측 실제 경기 기록 */}
        <div className="grid grid-cols-1 xl:grid-cols-[250px_minmax(0,1fr)] gap-5 items-start">
          <aside className="min-w-0 space-y-4 xl:sticky xl:top-20">
        {/* 날짜 / 구단 검색 */}
        <div className="p-4 bg-white border border-gray-100 rounded-3xl shadow-sm">

          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Search className="w-4 h-4 text-purple-600" />

            <h2 className="text-sm sm:text-base font-black text-gray-900">
              경기 찾아보기
            </h2>


            <button type="button" onClick={() => setFiltersCollapsed(v => !v)} aria-expanded={!filtersCollapsed} className="ml-auto rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-bold text-purple-700 hover:bg-purple-50">{filtersCollapsed ? '검색 조건 변경' : '조건 접기'}</button>
          </div>
          {filtersCollapsed ? <p className="text-xs font-medium text-gray-500">{selectedDate || '전체 날짜'} · {selectedTeam} · {filteredGames.length}경기 검색됨</p> : <>
          <div className="flex flex-col gap-3">

            {/* 날짜 선택 */}
            <div className="w-full min-w-0">
              <label
                htmlFor="game-search-date"
                className="block text-xs font-bold text-gray-600 mb-1.5"
              >
                경기 날짜
              </label>

              <div className="relative">
                <CalendarDays className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-purple-500 pointer-events-none" />

                <input
                  id="game-search-date"
                  type="date"
                  min="2026-01-01"
                  max="2026-12-31"
                  value={selectedDate}
                  onChange={(event) =>
                    handleDateChange(event.target.value)
                  }
                  className="w-full h-11 pl-10 pr-3 rounded-xl border border-gray-200 bg-gray-50 text-sm font-semibold text-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400"
                />
              </div>
            </div>

            {/* 구단 선택 */}
            <div className="w-full min-w-0">
              <label
                htmlFor="game-search-team"
                className="block text-xs font-bold text-gray-600 mb-1.5"
              >
                구단
              </label>

              <select
                id="game-search-team"
                value={selectedTeam}
                onChange={(event) =>
                  handleTeamChange(event.target.value)
                }
                className="w-full h-11 px-3 rounded-xl border border-gray-200 bg-gray-50 text-sm font-semibold text-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400 cursor-pointer"
              >
                {TEAMS.map((team) => (
                  <option
                    key={team}
                    value={TEAM_CODES[team] || team}
                  >
                    {team}
                  </option>
                ))}
              </select>
            </div>

            {/* 날짜 필터 해제 */}
            <button
              type="button"
              onClick={() => handleDateChange('')}
              className="h-11 px-4 rounded-xl bg-purple-50 hover:bg-purple-100 border border-purple-100 text-purple-700 text-sm font-bold transition-colors cursor-pointer whitespace-nowrap"
            >
              전체 날짜 보기
            </button>

            {/* 필터 초기화 */}
            <button
              type="button"
              onClick={() => {
                handleDateChange('2026-03-28');
                handleTeamChange('전체 구단');
              }}
              className="h-11 px-4 rounded-xl bg-gray-50 hover:bg-gray-100 border border-gray-200 text-gray-600 text-sm font-bold transition-colors cursor-pointer whitespace-nowrap"
            >
              초기화
            </button>
          </div>

          {/* 조회 결과 */}
          <div className="mt-4 pt-3 border-t border-gray-100 flex flex-col gap-1 text-xs">
            <span className="font-bold text-gray-600">
              검색 결과{' '}
              <span className="text-purple-700">
                {filteredGames.length}경기
              </span>
            </span>

            <span className="text-gray-400">
              전체 {games.length}경기 중
              {selectedDate
                ? ` · ${selectedDate}`
                : ' · 전체 날짜'}
              {' · '}
              {selectedTeam}
            </span>
          </div>
          </>}
        </div>

        {/* 목록 로딩 */}
        {isLoadingGames && (
          <div className="mb-6 p-8 bg-white border border-gray-100 rounded-3xl flex items-center justify-center gap-3">
            <LoaderCircle className="w-6 h-6 text-purple-600 animate-spin" />
            <span className="text-sm font-bold text-gray-600">
              경기 목록 불러오는 중...
            </span>
          </div>
        )}

        {/* 경기 목록 오류 */}
        {listError && !isLoadingGames && (
          <div className="mb-6 p-5 bg-red-50 border border-red-100 rounded-2xl text-red-700">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm font-bold">
                {listError}
              </span>
            </div>

            <button
              type="button"
              onClick={handleRetry}
              className="mt-3 flex items-center gap-2 bg-white rounded-xl border border-red-200 px-3 py-2 text-xs font-bold cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              다시 시도
            </button>
          </div>
        )}

        {/* 검색 결과 없음 */}
        {!isLoadingGames &&
          !listError &&
          filteredGames.length === 0 && (
            <div className="mb-6 p-10 bg-white rounded-3xl border border-gray-100 text-center">
              <CalendarDays className="w-9 h-9 text-gray-300 mx-auto mb-3" />

              <p className="font-bold text-gray-700">
                선택한 조건에 맞는 경기가 없어요.
              </p>

              <p className="text-xs text-gray-400 mt-2">
                다른 날짜나 구단을 선택해 보세요.
              </p>
            </div>
          )}

        {/* 경기 카드 목록 */}
        {!isLoadingGames &&
          displayedGames.length > 0 && (
            <>
              <RecentGamesBar
                games={displayedGames}
                selectedGameId={selectedGameId}
                onSelectGame={handleSelectGame}
              />

              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4 mb-6">
                  <button
                    type="button"
                    disabled={page === 1}
                    onClick={() =>
                      setPage((previous) =>
                        Math.max(1, previous - 1)
                      )
                    }
                    className="flex items-center gap-1 px-3 py-2 bg-white border border-gray-200 rounded-xl text-xs font-bold text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-purple-50 cursor-pointer"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    이전
                  </button>

                  <span className="text-xs font-bold text-gray-600">
                    {page} / {totalPages} 페이지
                  </span>

                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() =>
                      setPage((previous) =>
                        Math.min(totalPages, previous + 1)
                      )
                    }
                    className="flex items-center gap-1 px-3 py-2 bg-white border border-gray-200 rounded-xl text-xs font-bold text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-purple-50 cursor-pointer"
                  >
                    다음
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </>
          )}

          </aside>
          <div className="min-w-0">
        {/* 상세 경기 기록 로딩 */}
        {isLoadingPlays && gameMatchesFilter && (
          <div className="mb-6 bg-white border border-gray-100 rounded-3xl p-10 flex flex-col items-center justify-center gap-3">
            <LoaderCircle className="w-8 h-8 text-purple-600 animate-spin" />

            <p className="text-sm font-bold text-gray-600">
              선택한 경기의 타석·투구 기록을 불러오는 중...
            </p>
          </div>
        )}

        {/* 경기 상세 오류 */}
        {gameError &&
          !isLoadingPlays &&
          gameMatchesFilter && (
            <div className="mb-6 p-5 rounded-2xl bg-red-50 border border-red-100 text-red-700">
              <p className="text-sm font-bold">
                {gameError}
              </p>

              <button
                type="button"
                onClick={handleRetry}
                className="mt-3 text-xs font-bold underline cursor-pointer"
              >
                다시 시도
              </button>
            </div>
          )}

        {/* 실제 경기 화면 */}
        {canShowGame &&
          currentAtBat &&
          summary &&
          gameData && (
            <>
              <GameScoreHeader summary={summary} />

              {/* 한 화면에서 이닝 목록과 선택 타석 상세를 같이 확인 */}
              <div className="grid grid-cols-1 2xl:grid-cols-12 gap-5 items-start mt-5">
                <div className="2xl:col-span-6 min-w-0">
                  <InningPlaysHistory
                    atBats={atBats}
                    selectedAtBatId={selectedAtBatId}
                    onSelectAtBat={handleSelectAtBat}
                    onPrevAtBat={handlePrevAtBat}
                    onNextAtBat={handleNextAtBat}
                    hasPrev={currentAtBatIndex > 0}
                    hasNext={currentAtBatIndex >= 0 && currentAtBatIndex < atBats.length - 1}
                    awayTeam={gameData.game.away}
                    homeTeam={gameData.game.home}
                  />
                </div>
                <div className="2xl:col-span-6 min-w-0 2xl:sticky 2xl:top-20 self-start">
                  <CurrentAtBatCard
                    key={currentAtBat.id}
                    atBat={currentAtBat}
                    onAskWhy={() => setAiNotice(previous => !previous)}
                    gameId={selectedGameId}
                    playId={currentAtBat.resultPlayId}
                    onNavigate={onNavigate}
                    isAiExplaining={aiNotice}
                  />
                </div>
              </div>
              <div className="mt-3 text-center text-xs text-gray-400">
                전체 {atBats.length}개 타석 중{' '}
                {currentAtBatIndex + 1}번째 타석
                {' · '}
                플레이 순번 {currentAtBat.startSeq}
                ~{currentAtBat.endSeq}
              </div>
            </>
          )}
          </div>
        </div>
      </div>
    </div>
  );
}
