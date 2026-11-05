/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface HighlightVideo {
  videoUrl: string;
  durationSec: number;
  durationFormatted: string;
  thumbnailPlaceholderUrl?: string;
  thumbnailBadgeText: string;
}

export interface HighlightPriorContext {
  score: string;
  inning: string;
  outs: string;
  runners: string;
}

export interface HighlightResultContext {
  action: string;
  scoredRunners: string;
  summary: string;
}

export interface HighlightItem {
  id: string;
  gameId: string;
  sceneNumber: string; // "01", "02", etc.
  inning: string;
  playerName: string;
  playerTeam: string;
  playResult: string;
  playShortSummary: string;
  video: HighlightVideo;
  context: {
    priorSituation: HighlightPriorContext;
    resultSituation: HighlightResultContext;
    flowSteps: string[];
  };
  aiExplanation: {
    summary: string;
    keyTerms: string[];
  };
}

export interface HighlightGame {
  id: string;
  date: string;
  homeTeam: string;
  awayTeam: string;
  scoreDisplay: string;
  title: string;
  scenesCount: number;
  stadium: string;
}

export const MOCK_HIGHLIGHT_GAMES: HighlightGame[] = [
  {
    id: 'game-0930',
    date: '09/30',
    homeTeam: 'KT',
    awayTeam: 'KIA',
    scoreDisplay: 'KT 3 : 2 KIA',
    title: '09/30 KT vs KIA',
    scenesCount: 5,
    stadium: '수원 KT위즈파크',
  },
  {
    id: 'game-0912',
    date: '09/12',
    homeTeam: 'KIA',
    awayTeam: 'KT',
    scoreDisplay: 'KIA 2 : 6 KT',
    title: '09/12 KIA vs KT',
    scenesCount: 5,
    stadium: '광주 챔피언스필드',
  },
  {
    id: 'game-0620',
    date: '06/20',
    homeTeam: 'KIA',
    awayTeam: 'KT',
    scoreDisplay: 'KIA 9 : 10 KT',
    title: '06/20 KIA vs KT',
    scenesCount: 5,
    stadium: '광주 챔피언스필드',
  },
];

export const MOCK_HIGHLIGHT_SCENES: Record<string, HighlightItem[]> = {
  'game-0930': [
    {
      id: 'hl-0930-1',
      gameId: 'game-0930',
      sceneNumber: '01',
      inning: '2회초',
      playerName: '장준원',
      playerTeam: 'KT',
      playResult: '2루수 병살타 아웃',
      playShortSummary: '주자 1루 상황을 지워버린 완벽한 더블플레이',
      video: {
        videoUrl: '/videos/highlight-1.mp4',
        durationSec: 45,
        durationFormatted: '00:45',
        thumbnailBadgeText: '2회초 더블플레이',
      },
      context: {
        priorSituation: {
          score: 'KT 0 : 0 KIA',
          inning: '2회초',
          outs: '1아웃',
          runners: '1루 주자 있음',
        },
        resultSituation: {
          action: '장준원 2루수 땅볼 타격',
          scoredRunners: '2루 포스아웃 후 1루 송구 아웃',
          summary: '→ 이닝 종료 (병살타)',
        },
        flowSteps: [
          '1. 선두 타자 볼넷 출루',
          '2. 2루수 깊은 타구 깔끔한 포구',
          '3. 유격수 2루 터치',
          '4. 1루 송구 아웃으로 더블플레이 완성',
        ],
      },
      aiExplanation: {
        summary: `타자가 친 땅볼 타구가 2루수 정면으로 굴러갔어요.\n\n2루수가 빠르게 유격수에게 토스해 2루로 달리던 주자를 먼저 잡고, 유격수가 곧바로 1루에 던져 타자까지 한 번에 아웃시켰어요.\n공 하나로 아웃카운트 2개를 동시에 잡아 상대의 득점 기회를 완전히 차단한 수비 명장면이에요.`,
        keyTerms: ['#병살타', '#더블플레이', '#포스아웃', '#이닝종료'],
      },
    },
    {
      id: 'hl-0930-2',
      gameId: 'game-0930',
      sceneNumber: '02',
      inning: '5회초',
      playerName: '박재현',
      playerTeam: 'KIA',
      playResult: '만루 상황 3루타',
      playShortSummary: '2아웃 만루에서 터진 싹쓸이 역전 3루타',
      video: {
        videoUrl: '/videos/highlight-2.mp4',
        durationSec: 75,
        durationFormatted: '01:15',
        thumbnailBadgeText: '5회초 싹쓸이 3루타',
      },
      context: {
        priorSituation: {
          score: 'KIA 1 : 3 KT',
          inning: '5회초',
          outs: '2아웃',
          runners: '주자 만루',
        },
        resultSituation: {
          action: '박재현 3루타',
          scoredRunners: '주자 3명 득점',
          summary: '→ KIA 4 : 3 KT 역전',
        },
        flowSteps: [
          '1. 선두 타자 안타',
          '2. 볼넷으로 주자 추가',
          '3. 실책으로 만루',
          '4. 박재현 3루타',
        ],
      },
      aiExplanation: {
        summary: `이 장면 전까지 KIA는 2점 차로 뒤지고 있었어요.\n\n하지만 2아웃 만루 상황에서 박재현이 3루타를 치면서 세 명의 주자가 모두 홈에 들어왔고, 한 번의 타격으로 경기가 역전됐어요.\n\n그래서 이 장면은 경기 흐름이 완전히 바뀐 중요한 플레이예요.`,
        keyTerms: ['#만루', '#3루타', '#득점', '#역전'],
      },
    },
    {
      id: 'hl-0930-3',
      gameId: 'game-0930',
      sceneNumber: '03',
      inning: '9회말',
      playerName: '황대인',
      playerTeam: 'KIA',
      playResult: '끝내기 안타',
      playShortSummary: '9회말 2사에서 터진 극적인 끝내기 적시타',
      video: {
        videoUrl: '/videos/highlight-3.mp4',
        durationSec: 90,
        durationFormatted: '01:30',
        thumbnailBadgeText: '9회말 끝내기',
      },
      context: {
        priorSituation: {
          score: 'KT 2 : 2 KIA',
          inning: '9회말',
          outs: '2아웃',
          runners: '2루 주자 있음',
        },
        resultSituation: {
          action: '황대인 우중간 깊은 적시타',
          scoredRunners: '2루 주자 홈 쇄도 득점',
          summary: '→ KIA 3 : 2 KT 끝내기 승리',
        },
        flowSteps: [
          '1. 9회말 1사 후 2루타 출루',
          '2. 후속 타자 삼진 (2아웃)',
          '3. 2스트라이크 불리한 카운트',
          '4. 황대인 결정타로 경기 종료',
        ],
      },
      aiExplanation: {
        summary: `9회말 동점 상황에서 마지막 타자가 안타를 쳐 주자를 불러들이면 그 순간 경기가 즉시 끝나요.\n\n황대인의 타구가 외야로 빠져나가며 2루 주자가 홈을 밟았고, 추가 이닝 없이 바로 승리가 확정된 가장 짜릿한 순간이에요.`,
        keyTerms: ['#끝내기', '#적시타', '#서든데스', '#승리'],
      },
    },
    {
      id: 'hl-0930-4',
      gameId: 'game-0930',
      sceneNumber: '04',
      inning: '7회말',
      playerName: '박영현',
      playerTeam: 'KT',
      playResult: '3타자 연속 삼진',
      playShortSummary: '위기에서 세 타자를 연달아 헛스윙 삼진 처리',
      video: {
        videoUrl: '/videos/highlight-4.mp4',
        durationSec: 60,
        durationFormatted: '01:00',
        thumbnailBadgeText: '7회말 K-K-K',
      },
      context: {
        priorSituation: {
          score: 'KT 2 : 1 KIA',
          inning: '7회말',
          outs: '0아웃',
          runners: '1·3루 위기',
        },
        resultSituation: {
          action: '박영현 세 타자 연속 탈삼진',
          scoredRunners: '무실점 방어',
          summary: '→ 리드 수성 (이닝 종료)',
        },
        flowSteps: [
          '1. 무사 1·3루 실점 위기 등판',
          '2. 1번 타자 150km 직구 헛스윙 삼진',
          '3. 2번 타자 슬라이더 루킹 삼진',
          '4. 3번 타자 하이 패스트볼 삼진 종료',
        ],
      },
      aiExplanation: {
        summary: `주자가 1루와 3루에 모두 있어 안타 하나면 실점하는 절대적 위기였어요.\n\n투수 박영현이 최고 구속 150km의 강속구와 슬라이더로 세 명의 타자를 연속으로 헛스윙 삼진 처리해 점수를 단 1점도 주지 않고 막아낸 구원 역투예요.`,
        keyTerms: ['#연속삼진', '#위기탈출', '#탈삼진', '#구원투수'],
      },
    },
    {
      id: 'hl-0930-5',
      gameId: 'game-0930',
      sceneNumber: '05',
      inning: '8회초',
      playerName: '최형우',
      playerTeam: 'KIA',
      playResult: '동점 솔로 홈런',
      playShortSummary: '우측 담장을 훌쩍 넘긴 125m 대형 동점포',
      video: {
        videoUrl: '/videos/highlight-5.mp4',
        durationSec: 52,
        durationFormatted: '00:52',
        thumbnailBadgeText: '8회초 동점포',
      },
      context: {
        priorSituation: {
          score: 'KIA 1 : 2 KT',
          inning: '8회초',
          outs: '1아웃',
          runners: '주자 없음',
        },
        resultSituation: {
          action: '최형우 우월 솔로 홈런',
          scoredRunners: '타자 1명 득점',
          summary: '→ KIA 2 : 2 KT 동점 균형',
        },
        flowSteps: [
          '1. 8회초 1점 차 타이트한 접전',
          '2. 초구 볼, 2구 스트라이크 카운트',
          '3. 실투성 직구를 통타',
          '4. 우측 담장 넘기는 비거리 125m 홈런',
        ],
      },
      aiExplanation: {
        summary: `경기가 얼마 남지 않은 8회, 단 1점 차로 끌려가던 패배 직전의 분위기를 한 방에 뒤집은 솔로 홈런이에요.\n\n타자가 친 공이 담장을 완전히 넘어가며 타자 스스로 홈으로 돌아와 2:2 동점을 만들었습니다.`,
        keyTerms: ['#솔로홈런', '#동점포', '#장타', '#비거리'],
      },
    },
  ],
  'game-0912': [
    {
      id: 'hl-0912-1',
      gameId: 'game-0912',
      sceneNumber: '01',
      inning: '3회초',
      playerName: '강백호',
      playerTeam: 'KT',
      playResult: '2점 적시 2루타',
      playShortSummary: '초반 기세를 가져오는 우중간 장타',
      video: {
        videoUrl: '/videos/highlight-0912-1.mp4',
        durationSec: 50,
        durationFormatted: '00:50',
        thumbnailBadgeText: '3회초 적시 2루타',
      },
      context: {
        priorSituation: {
          score: 'KIA 0 : 0 KT',
          inning: '3회초',
          outs: '1아웃',
          runners: '1·2루 득점권',
        },
        resultSituation: {
          action: '강백호 우중간 가르는 2루타',
          scoredRunners: '주자 2명 득점',
          summary: '→ KT 2 : 0 KIA 선취 득점',
        },
        flowSteps: [
          '1. 연속 안타로 득점권 주자',
          '2. 강백호 타석 진입',
          '3. 3구째 우중간 가르는 장타',
          '4. 2루 주자, 1루 주자 연속 득점',
        ],
      },
      aiExplanation: {
        summary: `0:0 팽팽하던 승부에서 선취점이 터진 순간이에요. 강백호가 우중간을 가르는 2루타로 주자 2명을 모두 불러들여 승기를 잡았습니다.`,
        keyTerms: ['#2루타', '#적시타', '#선취점', '#득점권'],
      },
    },
    {
      id: 'hl-0912-2',
      gameId: 'game-0912',
      sceneNumber: '02',
      inning: '5회말',
      playerName: '나성범',
      playerTeam: 'KIA',
      playResult: '추격 솔로 홈런',
      playShortSummary: '중월 130m 대형 솔로 아치',
      video: {
        videoUrl: '/videos/highlight-0912-2.mp4',
        durationSec: 55,
        durationFormatted: '00:55',
        thumbnailBadgeText: '5회말 추격포',
      },
      context: {
        priorSituation: {
          score: 'KIA 0 : 3 KT',
          inning: '5회말',
          outs: '0아웃',
          runners: '주자 없음',
        },
        resultSituation: {
          action: '나성범 중앙 담장 넘기는 솔로포',
          scoredRunners: '1득점',
          summary: '→ KIA 1 : 3 KT 추격',
        },
        flowSteps: [
          '1. 3점 차 뒤진 5회말 선두타자',
          '2. 가운데 몰린 포크볼 포착',
          '3. 센터 깊숙한 홈런 타구',
        ],
      },
      aiExplanation: {
        summary: `침묵하던 타선에 활력을 불어넣는 대형 홈런이었어요. 점수 차를 좁히며 반격의 발판을 마련했습니다.`,
        keyTerms: ['#솔로홈런', '#추격포', '#장타'],
      },
    },
    {
      id: 'hl-0912-3',
      gameId: 'game-0912',
      sceneNumber: '03',
      inning: '7회초',
      playerName: '황재균',
      playerTeam: 'KT',
      playResult: '쐐기 3점 홈런',
      playShortSummary: '승부를 결정짓는 좌월 3점포',
      video: {
        videoUrl: '/videos/highlight-0912-3.mp4',
        durationSec: 65,
        durationFormatted: '01:05',
        thumbnailBadgeText: '7회초 쐐기포',
      },
      context: {
        priorSituation: {
          score: 'KIA 1 : 3 KT',
          inning: '7회초',
          outs: '1아웃',
          runners: '1·2루 찬스',
        },
        resultSituation: {
          action: '황재균 3점 홈런',
          scoredRunners: '3득점',
          summary: '→ KT 6 : 1 KIA 점수차 벌림',
        },
        flowSteps: [
          '1. 안타와 야수선택으로 찬스',
          '2. 풀카운트 명승부',
          '3. 좌측 스탠드 꽂히는 3점 홈런',
        ],
      },
      aiExplanation: {
        summary: `KIA의 추격 의지를 꺾는 결정적인 한 방이었어요. 3점을 보태며 사실상 승부에 쐐기를 박았습니다.`,
        keyTerms: ['#3점홈런', '#쐐기포', '#클러치'],
      },
    },
    {
      id: 'hl-0912-4',
      gameId: 'game-0912',
      sceneNumber: '04',
      inning: '8회말',
      playerName: '김도영',
      playerTeam: 'KIA',
      playResult: '우전 안타 & 도루',
      playShortSummary: '빠른 발로 2루를 훔쳐낸 기동력 야구',
      video: {
        videoUrl: '/videos/highlight-0912-4.mp4',
        durationSec: 40,
        durationFormatted: '00:40',
        thumbnailBadgeText: '8회말 도루 성공',
      },
      context: {
        priorSituation: {
          score: 'KIA 1 : 6 KT',
          inning: '8회말',
          outs: '1아웃',
          runners: '주자 없음',
        },
        resultSituation: {
          action: '안타 출루 후 2루 도루 성공',
          scoredRunners: '득점권 찬스 생성',
          summary: '→ 1사 2루',
        },
        flowSteps: ['1. 깔끔한 우전 안타', '2. 초구 투구 시 즉시 스타트', '3. 헤드퍼스트 슬라이딩 세이프'],
      },
      aiExplanation: {
        summary: `타자가 공이 투수 손을 떠나자마자 2루로 내달려 세이프를 만들어냈어요. 팀 분위기를 끌어올리는 주루 센스였습니다.`,
        keyTerms: ['#도루', '#주루플레이', '#세이프'],
      },
    },
    {
      id: 'hl-0912-5',
      gameId: 'game-0912',
      sceneNumber: '05',
      inning: '9회말',
      playerName: '김민수',
      playerTeam: 'KT',
      playResult: '경기 종료 삼진',
      playShortSummary: '루킹 삼진으로 경기 마무리',
      video: {
        videoUrl: '/videos/highlight-0912-5.mp4',
        durationSec: 35,
        durationFormatted: '00:35',
        thumbnailBadgeText: '9회말 세이브',
      },
      context: {
        priorSituation: {
          score: 'KIA 2 : 6 KT',
          inning: '9회말',
          outs: '2아웃',
          runners: '주자 없음',
        },
        resultSituation: {
          action: '바깥쪽 꽉 찬 제구 루킹 삼진',
          scoredRunners: '3아웃',
          summary: '→ KT 6 : 2 승리 종료',
        },
        flowSteps: ['1. 9회말 2아웃 마지막 타석', '2. 바깥쪽 보더라인 제구', '3. 타자 배트 멈칫 루킹 삼진'],
      },
      aiExplanation: {
        summary: `마지막 아웃카운트를 잡는 순간 배트조차 나오지 못할 정도로 완벽한 코스로 꽂힌 삼진이에요. KT가 6:2로 승리를 챙겼습니다.`,
        keyTerms: ['#루킹삼진', '#경기종료', '#세이브'],
      },
    },
  ],
  'game-0620': [
    {
      id: 'hl-0620-1',
      gameId: 'game-0620',
      sceneNumber: '01',
      inning: '1회초',
      playerName: '소형준',
      playerTeam: 'KT',
      playResult: '삼자범퇴 이닝',
      playShortSummary: '공 9개로 1회를 완벽하게 정리',
      video: {
        videoUrl: '/videos/highlight-0620-1.mp4',
        durationSec: 42,
        durationFormatted: '00:42',
        thumbnailBadgeText: '1회초 삼자범퇴',
      },
      context: {
        priorSituation: { score: 'KIA 0 : 0 KT', inning: '1회초', outs: '0아웃', runners: '주자 없음' },
        resultSituation: { action: '연속 범타 처리', scoredRunners: '0득점', summary: '→ 공 9개 이닝 종료' },
        flowSteps: ['1. 땅볼 아웃', '2. 외야 뜬공 아웃', '3. 삼진 아웃'],
      },
      aiExplanation: {
        summary: `선발투수가 단 9개의 투구로 세 타자를 연달아 잡아내며 깔끔하게 경기를 출발했어요.`,
        keyTerms: ['#삼자범퇴', '#선발투수', '#이닝종료'],
      },
    },
    {
      id: 'hl-0620-2',
      gameId: 'game-0620',
      sceneNumber: '02',
      inning: '4회말',
      playerName: '김선빈',
      playerTeam: 'KIA',
      playResult: '다이빙 캐치 호수비',
      playShortSummary: '중전 안타성 타구를 건져낸 그림 같은 수비',
      video: {
        videoUrl: '/videos/highlight-0620-2.mp4',
        durationSec: 48,
        durationFormatted: '00:48',
        thumbnailBadgeText: '4회말 호수비',
      },
      context: {
        priorSituation: { score: 'KIA 4 : 5 KT', inning: '4회말', outs: '2아웃', runners: '2루 주자 있음' },
        resultSituation: { action: '2루수 몸 날려 다이빙 캐치', scoredRunners: '실점 위기 방어', summary: '→ 1루 송구 아웃' },
        flowSteps: ['1. 2루 베이스 옆 빠져나가는 빠른 타구', '2. 다이빙으로 글러브 포구', '3. 일어서며 정확한 1루 송구'],
      },
      aiExplanation: {
        summary: `빠져나갔다면 무조건 1점을 주는 타구였지만, 2루수 김선빈이 온몸을 던져 낚아채며 실점을 막아냈습니다.`,
        keyTerms: ['#다이빙캐치', '#호수비', '#실점위기방어'],
      },
    },
    {
      id: 'hl-0620-3',
      gameId: 'game-0620',
      sceneNumber: '03',
      inning: '6회초',
      playerName: '로하스',
      playerTeam: 'KT',
      playResult: '투런 역전 홈런',
      playShortSummary: '경기 리드를 되찾아오는 시원한 투런포',
      video: {
        videoUrl: '/videos/highlight-0620-3.mp4',
        durationSec: 58,
        durationFormatted: '00:58',
        thumbnailBadgeText: '6회초 역전 투런',
      },
      context: {
        priorSituation: { score: 'KIA 7 : 6 KT', inning: '6회초', outs: '1아웃', runners: '1루 주자' },
        resultSituation: { action: '우월 2점 홈런', scoredRunners: '2득점', summary: '→ KT 8 : 7 KIA 역전' },
        flowSteps: ['1. 안타 출루', '2. 초구 직구 강타', '3. 역전 홈런'],
      },
      aiExplanation: {
        summary: `한 점 뒤지던 상황에서 단숨에 역전을 만들어낸 시원한 홈런이었습니다.`,
        keyTerms: ['#투런홈런', '#역전타', '#장타'],
      },
    },
    {
      id: 'hl-0620-4',
      gameId: 'game-0620',
      sceneNumber: '04',
      inning: '8회초',
      playerName: '배정대',
      playerTeam: 'KT',
      playResult: '2타점 적시타',
      playShortSummary: '치열한 난타전 속 승리를 굳히는 안타',
      video: {
        videoUrl: '/videos/highlight-0620-4.mp4',
        durationSec: 52,
        durationFormatted: '00:52',
        thumbnailBadgeText: '8회초 적시타',
      },
      context: {
        priorSituation: { score: 'KIA 8 : 8 KT', inning: '8회초', outs: '2아웃', runners: '2·3루' },
        resultSituation: { action: '중전 적시 안타', scoredRunners: '2득점', summary: '→ KT 10 : 8 리드' },
        flowSteps: ['1. 연속 안타로 찬스', '2. 2사 후 클러치 안타', '3. 2명 주자 여유있게 득점'],
      },
      aiExplanation: {
        summary: `8:8 동점 균형을 깨고 승부를 가져온 배정대의 결정타였습니다.`,
        keyTerms: ['#클러치히터', '#적시타', '#승부처'],
      },
    },
    {
      id: 'hl-0620-5',
      gameId: 'game-0620',
      sceneNumber: '05',
      inning: '9회말',
      playerName: '박영현',
      playerTeam: 'KT',
      playResult: '1점차 극적 세이브',
      playShortSummary: '10:9 살얼음판 승부를 지켜낸 마지막 아웃카운트',
      video: {
        videoUrl: '/videos/highlight-0620-5.mp4',
        durationSec: 62,
        durationFormatted: '01:02',
        thumbnailBadgeText: '9회말 1점차 세이브',
      },
      context: {
        priorSituation: { score: 'KIA 9 : 10 KT', inning: '9회말', outs: '2아웃', runners: '주자 2루 동점위기' },
        resultSituation: { action: '유격수 땅볼 유도 포구 아웃', scoredRunners: '3아웃', summary: '→ KT 10 : 9 승리' },
        flowSteps: ['1. 1점 차 2사 2루 위기', '2. 몸쪽 직구로 타이밍 뺏음', '3. 1루 송구 아웃 경기 종료'],
      },
      aiExplanation: {
        summary: `양 팀 합쳐 19점이 터진 치열한 타격전의 마침표를 찍은 마지막 투구였습니다. 1점 차 리드를 지켜내며 승리를 확정지었습니다.`,
        keyTerms: ['#세이브', '#1점차승리', '#접전'],
      },
    },
  ],
};
