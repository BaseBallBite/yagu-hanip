/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface PitchDetail {
  pitchNumber: number;
  pitchType: string;
  speedKm: number;
  result: string;
  isStrike: boolean;
  zoneLocation: {
    x: number; // percentage from left (0 - 100)
    y: number; // percentage from top (0 - 100)
  };
  description: string;
}

export interface AtBatPlay {
  id: string;
  batterName: string;
  batterPosition: string;
  batterTeam: string;
  pitcherName: string;
  pitcherTeam: string;
  resultText: string;
  resultBadge: string;
  pitchCountText: string;
  pitchesCount: number;
  balls: number;
  strikes: number;
  outs: number;
  currentPitch: PitchDetail;
  pitchesHistory: PitchDetail[];
  aiExplanation: {
    summary: string;
    keyTerms: string[];
    evidenceSources: string[];
  };
}

export interface RecentGameItem {
  id: string;
  homeTeam: string;
  homeScore: number;
  awayTeam: string;
  awayScore: number;
  date: string;
  status: string; // e.g., '종료', '진행중'
  isCurrentGame?: boolean;
}

export interface CurrentGameSummary {
  homeTeam: string;
  homeScore: number;
  awayTeam: string;
  awayScore: number;
  inning: string;
  outsCount: number; // 2
  runners: {
    first: boolean;
    second: boolean;
    third: boolean;
  };
  date: string;
  stadium: string;
  balls: number;
  strikes: number;
}

// Recent Games Mock Data
export const MOCK_RECENT_GAMES: RecentGameItem[] = [
  {
    id: 'game-1',
    homeTeam: 'KT',
    homeScore: 3,
    awayTeam: 'KIA',
    awayScore: 2,
    date: '09/30',
    status: '9회초 진행중',
    isCurrentGame: true,
  },
  {
    id: 'game-2',
    homeTeam: 'KIA',
    homeScore: 2,
    awayTeam: 'KT',
    awayScore: 6,
    date: '09/12',
    status: '종료',
  },
  {
    id: 'game-3',
    homeTeam: 'KIA',
    homeScore: 9,
    awayTeam: 'KT',
    awayScore: 10,
    date: '06/20',
    status: '종료',
  },
];

// Current Game Header Info
export const MOCK_GAME_SUMMARY: CurrentGameSummary = {
  homeTeam: 'KT',
  homeScore: 3,
  awayTeam: 'KIA',
  awayScore: 2,
  inning: '9회초',
  outsCount: 1, // 해당 타석의 삼진 직후 1아웃
  runners: {
    first: true, // 1루 주자 있음
    second: false,
    third: false,
  },
  date: '09/30',
  stadium: '수원 KT위즈파크',
  balls: 2,
  strikes: 3,
};

// 9회초 KIA 공격 At-Bats (시연용 Mock, 실제 경기 API와 별개)
export const MOCK_AT_BATS: AtBatPlay[] = [
  {
    id: 'atbat-1',
    batterName: '황대인',
    batterPosition: '1루수 · 4번 타자',
    batterTeam: 'KIA',
    pitcherName: '박영현',
    pitcherTeam: 'KT',
    resultText: '삼진 아웃',
    resultBadge: '→ 삼진 아웃',
    pitchCountText: '6구',
    pitchesCount: 6,
    balls: 2,
    strikes: 3,
    outs: 2,
    currentPitch: {
      pitchNumber: 6,
      pitchType: '슬라이더',
      speedKm: 136,
      result: '헛스윙',
      isStrike: true,
      zoneLocation: {
        x: 68, // slightly outside-right
        y: 84, // down below strike zone bottom edge
      },
      description: '스트라이크 존 하단 바깥쪽으로 날카롭게 떨어지는 결정구 슬라이더',
    },
    pitchesHistory: [
      { pitchNumber: 1, pitchType: '직구', speedKm: 147, result: '스트라이크', isStrike: true, zoneLocation: { x: 45, y: 35 }, description: '한가운데 높은 직구' },
      { pitchNumber: 2, pitchType: '슬라이더', speedKm: 134, result: '볼', isStrike: false, zoneLocation: { x: 85, y: 75 }, description: '바깥쪽 빠지는 볼' },
      { pitchNumber: 3, pitchType: '직구', speedKm: 149, result: '파울', isStrike: true, zoneLocation: { x: 30, y: 50 }, description: '몸쪽 깊은 코스 파울' },
      { pitchNumber: 4, pitchType: '체인지업', speedKm: 129, result: '볼', isStrike: false, zoneLocation: { x: 15, y: 90 }, description: '낮게 떨어지는 볼' },
      { pitchNumber: 5, pitchType: '직구', speedKm: 148, result: '파울', isStrike: true, zoneLocation: { x: 55, y: 25 }, description: '하이 패스트볼 커트' },
      { pitchNumber: 6, pitchType: '슬라이더', speedKm: 136, result: '헛스윙 삼진', isStrike: true, zoneLocation: { x: 68, y: 84 }, description: '존 아래로 떨어지는 결정구 유인' },
    ],
    aiExplanation: {
      summary: `슬라이더가 스트라이크존 아래쪽으로 떨어지면서 타자의 배트가 헛돌았어요.\n\n스트라이크가 3개가 되어 삼진 아웃이 된 상황이에요.`,
      keyTerms: ['#슬라이더', '#헛스윙', '#삼진'],
      evidenceSources: [
        '현재 투구 기록 (6구 슬라이더 136km/h)',
        '볼/스트라이크 카운트 (2볼 2스트라이크 후 헛스윙)',
        '현재 타석 결과 (삼진 아웃 판정)',
        '야구 규칙 정보 (스트라이크 3개 누적 시 아웃 규정)',
      ],
    },
  },
  {
    id: 'atbat-2',
    batterName: '하주석',
    batterPosition: '유격수 · 5번 타자',
    batterTeam: 'KIA',
    pitcherName: '박영현',
    pitcherTeam: 'KT',
    resultText: '2루수 라인드라이브 아웃',
    resultBadge: '→ 2루수 직선타 아웃',
    pitchCountText: '3구',
    pitchesCount: 3,
    balls: 1,
    strikes: 1,
    outs: 1,
    currentPitch: {
      pitchNumber: 3,
      pitchType: '직구',
      speedKm: 148,
      result: '인플레이 타구 아웃',
      isStrike: true,
      zoneLocation: {
        x: 52,
        y: 45,
      },
      description: '존 한가운데 몰린 직구를 타격했으나 2루수 정면으로 날아간 직선타',
    },
    pitchesHistory: [
      { pitchNumber: 1, pitchType: '체인지업', speedKm: 131, result: '스트라이크', isStrike: true, zoneLocation: { x: 40, y: 60 }, description: '존 낮은 코스' },
      { pitchNumber: 2, pitchType: '슬라이더', speedKm: 135, result: '볼', isStrike: false, zoneLocation: { x: 90, y: 50 }, description: '바깥쪽 높게 빠짐' },
      { pitchNumber: 3, pitchType: '직구', speedKm: 148, result: '타격 아웃', isStrike: true, zoneLocation: { x: 52, y: 45 }, description: '2루수 정면 라인드라이브' },
    ],
    aiExplanation: {
      summary: `타자가 배트 중심에 공을 잘 맞혔지만, 타구가 2루수 수비수의 글러브로 바로 날아갔어요.\n\n공이 땅에 닿기 전에 수비수가 바로 잡아 '라인드라이브(직선타) 아웃'이 되었습니다.`,
      keyTerms: ['#라인드라이브', '#직선타', '#아웃'],
      evidenceSources: [
        '타구 궤적 기록 (수평 직선 타구)',
        '수비 위치 (2루수 포구 완료)',
        '야구 규칙 정보 (노바운드 포구 즉시 타자 아웃)',
      ],
    },
  },
  {
    id: 'atbat-3',
    batterName: '한준수',
    batterPosition: '포수 · 6번 타자',
    batterTeam: 'KIA',
    pitcherName: '박영현',
    pitcherTeam: 'KT',
    resultText: '좌익수 플라이 아웃',
    resultBadge: '→ 좌익수 뜬공 아웃',
    pitchCountText: '2구',
    pitchesCount: 2,
    balls: 0,
    strikes: 1,
    outs: 0,
    currentPitch: {
      pitchNumber: 2,
      pitchType: '포심 직구',
      speedKm: 146,
      result: '인플레이 외야 뜬공',
      isStrike: true,
      zoneLocation: {
        x: 35,
        y: 28,
      },
      description: '높은 하이 패스트볼에 배트 윗부분이 맞아 높게 뜬 뜬공 타구',
    },
    pitchesHistory: [
      { pitchNumber: 1, pitchType: '슬라이더', speedKm: 133, result: '파울', isStrike: true, zoneLocation: { x: 60, y: 70 }, description: '우측 파울' },
      { pitchNumber: 2, pitchType: '포심 직구', speedKm: 146, result: '외야 뜬공', isStrike: true, zoneLocation: { x: 35, y: 28 }, description: '좌익수 플라이 아웃' },
    ],
    aiExplanation: {
      summary: `투수의 빠른 공에 배트가 밀리면서 공이 높이 솟구쳤어요.\n\n좌익수가 여유 있게 낙구 지점을 잡아내면서 뜬공(플라이) 아웃이 선언되었습니다.`,
      keyTerms: ['#플라이아웃', '#뜬공', '#외야수'],
      evidenceSources: [
        '타구 발사각 (42도 높은 포물선)',
        '수비 위치 (좌익수 포구)',
        '야구 규칙 정보 (뜬공 포구 시 타자 아웃)',
      ],
    },
  },
];
