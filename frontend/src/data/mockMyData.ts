/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { MOCK_STANDINGS, TeamStanding } from './mockRankingData';

export type ExplanationLevel = 'beginner' | 'standard' | 'detailed';

export interface SavedQuestion {
  id: string;
  question: string;
  category: '경기 해설' | '야구사전';
  savedDate: string; // e.g. "09/30"
  previewAnswer: string;
  sourceContext?: string;
  targetPath: '/game' | '/dictionary' | '/highlights';
  termId?: string;
}

export interface RecentGameActivity {
  id: string;
  date: string; // e.g. "09/30"
  matchup: string; // e.g. "KT vs KIA"
  homeTeam: string;
  awayTeam: string;
  score: string; // e.g. "3 : 2"
  resultBadge?: string;
  highlightSummary: string;
}

export interface RecentSearchTerm {
  id: string;
  name: string;
  category: string;
  description: string;
}

export const INITIAL_SAVED_QUESTIONS: SavedQuestion[] = [
  {
    id: 'sq-1',
    question: '병살은 왜 아웃이 두 개인가요?',
    category: '야구사전',
    savedDate: '09/30',
    previewAnswer: '타자가 친 공 하나로 수비 팀이 연속해서 2명의 공격 주자(또는 타자와 주자)를 한꺼번에 아웃시키는 것을 말해요. 수비에는 최고의 장면, 공격에는 가장 아쉬운 순간이에요.',
    sourceContext: 'KBO 공인야구규칙 9.11 더블플레이',
    targetPath: '/dictionary',
    termId: 'double-play'
  },
  {
    id: 'sq-2',
    question: '왜 이 상황에서 주자가 움직였나요?',
    category: '경기 해설',
    savedDate: '09/30',
    previewAnswer: '9회말 2아웃 볼카운트 3-2(풀카운트)에서는 투수가 공을 던지는 순간 모든 주자가 무조건 다음 베이스로 달립니다. 삼진이면 이닝 종료, 볼넷이면 자동 진루, 안타면 득점 확률을 극대화하기 때문이에요.',
    sourceContext: '09/30 KT vs KIA 9회말 2사 만루 상황',
    targetPath: '/game'
  },
  {
    id: 'sq-3',
    question: '낫아웃은 언제 가능한가요?',
    category: '야구사전',
    savedDate: '09/29',
    previewAnswer: '2스트라이크 후 3번째 스트라이크를 포수가 바로 잡지 못하고 놓쳤을 때, 주자가 1루에 없거나(또는 2아웃 상황), 타자가 1루로 전력 질주해 아웃을 면하려는 규칙이에요.',
    sourceContext: 'KBO 공인야구규칙 5.05(a)(2)',
    targetPath: '/dictionary',
    termId: 'strikeout-not-out'
  }
];

export const MOCK_RECENT_GAMES: RecentGameActivity[] = [
  {
    id: 'game-1',
    date: '09/30',
    matchup: 'KT vs KIA',
    homeTeam: 'KT',
    awayTeam: 'KIA',
    score: '3 : 2',
    resultBadge: '종료',
    highlightSummary: '박영현 9회말 1점차 만루 위기 극적 세이브'
  },
  {
    id: 'game-2',
    date: '09/12',
    matchup: 'KIA vs KT',
    homeTeam: 'KIA',
    awayTeam: 'KT',
    score: '5 : 4',
    resultBadge: '종료',
    highlightSummary: '김도영 8회말 역전 결승 투런 홈런'
  },
  {
    id: 'game-3',
    date: '06/20',
    matchup: 'KIA vs KT',
    homeTeam: 'KIA',
    awayTeam: 'KT',
    score: '1 : 7',
    resultBadge: '종료',
    highlightSummary: '쿠에바스 7이닝 1실점 퀄리티스타트 플러스'
  }
];

export const MOCK_RECENT_TERMS: RecentSearchTerm[] = [
  {
    id: 'term-dp',
    name: '병살',
    category: '기본 규칙',
    description: '공 하나로 아웃 2개를 동시에 잡는 플레이'
  },
  {
    id: 'term-no',
    name: '낫아웃',
    category: '특수 규칙',
    description: '3번째 스트라이크를 포수가 놓쳤을 때 1루로 뛰는 상황'
  },
  {
    id: 'term-sl',
    name: '슬라이더',
    category: '투구 구종',
    description: '직구처럼 날아가다 홈플레이트 앞에서 날카롭게 꺾이는 공'
  },
  {
    id: 'term-if',
    name: '인필드 플라이',
    category: '세부 규칙',
    description: '내야 뜬공 때 수비의 고의 낙구를 방지하기 위한 타자 즉시 아웃 규칙'
  }
];

// Helper to look up team info from standings or fallback defaults
export function getFavoriteTeamInfo(teamName: string | null | undefined): TeamStanding | null {
  if (!teamName || teamName === 'NONE' || teamName === 'none') {
    return null;
  }
  const clean = teamName.trim();
  const found = MOCK_STANDINGS.find(
    (t) => t.name.toLowerCase() === clean.toLowerCase() || t.fullName.includes(clean)
  );
  if (found) {
    return found;
  }

  // Fallback for KIA if not matched
  if (clean.toUpperCase() === 'KIA') {
    return (
      MOCK_STANDINGS.find((t) => t.id === 'kia') || {
        rank: 3,
        id: 'kia',
        name: 'KIA',
        fullName: 'KIA 타이거즈',
        initial: 'KIA',
        primaryColor: '#C3042D',
        lightBg: '#FFF1F2',
        logo: '/logos/kia.png',
        wins: 80,
        draws: 2,
        losses: 62,
        winRate: '.563',
        gamesBehind: '11.5',
        last5: ['W', 'L', 'W', 'W', 'L'],
        last5Record: '최근 5경기 3승 2패',
        analysisComment: '안정적인 선발진과 강한 타선을 바탕으로 상위권 경쟁을 유지하고 있어요.',
        stadium: '광주-기아 챔피언스필드'
      }
    );
  }

  return null;
}
