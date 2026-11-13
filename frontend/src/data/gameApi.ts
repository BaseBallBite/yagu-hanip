
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 *
 * B2/B4 실제 경기 API 연결
 */

import type {
  AtBatPlay,
  CurrentGameSummary,
  PitchDetail,
  RecentGameItem,
} from './mockGameData';

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000';

export interface GameRecord {
  game_id: string;
  game_date: string;
  start_time?: string;
  away: string;
  home: string;
  away_score: number;
  home_score: number;
  status: string;
  play_count: number;
}

interface GameListResponse {
  count: number;
  games: GameRecord[];
}

interface BaseballState {
  outs: number;
  runners: {
    '1': string | null;
    '2': string | null;
    '3': string | null;
  };
  score: {
    away: number;
    home: number;
  };
}

interface PitchCount {
  balls: number;
  strikes: number;
}

interface ApiPitch {
  plate_appearance_id?: string | null;
  pitch_number?: number | null;
  pitch_type_raw?: string | null;
  pitch_type?: string | null;
  speed?: number | null;
  result_text?: string | null;
  visualization_status?: string | null;
  count_before?: PitchCount | null;
  count_after?: PitchCount | null;
  zone?: {
    x_ft: number;
    height_ft: number;
    top_ft: number;
    bottom_ft: number;
  } | null;
}

interface ApiPlay {
  seq: number;
  inning: number;
  half: 'top' | 'bottom';
  event_type: string;
  description: string;
  batter?: string | null;
  pitcher?: string | null;
  state_before?: BaseballState | null;
  state_after?: BaseballState | null;
  pitch?: ApiPitch | null;
}

interface PlaysResponse {
  game_id: string;
  away: string;
  home: string;
  count: number;
  plays: ApiPlay[];
}

export interface RealAtBat extends AtBatPlay {
  inning: number;
  half: 'top' | 'bottom';
  stateAfter: BaseballState;
  startSeq: number;
  endSeq: number;
}

export interface GameScreenData {
  game: GameRecord;
  atBats: RealAtBat[];
}

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);

  if (!response.ok) {
    if (response.status === 503) {
      throw new Error(
        '경기 DB에 연결할 수 없어요. 백엔드 서버와 SQLite 파일을 확인해 주세요.'
      );
    }

    throw new Error(
      `경기 API 요청에 실패했어요. (HTTP ${response.status})`
    );
  }

  return (await response.json()) as T;
}

// 전체 경기 목록 조회: 특정 날짜로 고정하지 않음
export async function fetchGames(): Promise<GameRecord[]> {
  const response = await requestJson<GameListResponse>('/games');

  return [...response.games].sort((a, b) => {
    const dateCompare = b.game_date.localeCompare(a.game_date);

    return dateCompare !== 0
      ? dateCompare
      : a.game_id.localeCompare(b.game_id);
  });
}

export function toRecentGame(
  game: GameRecord
): RecentGameItem {
  return {
    id: game.game_id,
    homeTeam: game.home,
    homeScore: game.home_score,
    awayTeam: game.away,
    awayScore: game.away_score,
    date: game.game_date.slice(5).replace('-', '/'),
    status: `경기 종료 · ${game.status}`,
  };
}

const AT_BAT_RESULT_EVENTS = new Set([
  'single',
  'double',
  'triple',
  'home_run',
  'walk',
  'intentional_walk',
  'hit_by_pitch',
  'strikeout',
  'flyout',
  'groundout',
  'lineout',
  'popout',
  'field_out',
  'double_play',
  'triple_play',
  'grounded_into_double_play',
  'fielders_choice',
  'fielders_choice_out',
  'sacrifice_fly',
  'sacrifice_bunt',
  'sac_fly',
  'sac_bunt',
  'error',
  'reached_on_error',
  'catcher_interference',
  'bunt_out',
  'other_out',
]);

const FOLLOW_UP_EVENTS = new Set([
  'runner_advance',
  'run_scored',
  'runner_out',
  'steal',
  'caught_stealing',
]);

function emptyState(): BaseballState {
  return {
    outs: 0,
    runners: {
      '1': null,
      '2': null,
      '3': null,
    },
    score: {
      away: 0,
      home: 0,
    },
  };
}

type VisualPitch = PitchDetail & {
  zoneAvailable: boolean;
};

function toPitchDetail(pitch: ApiPitch): VisualPitch {
  const zone = pitch.zone;

  const available =
    pitch.visualization_status === 'available' &&
    zone != null &&
    Number.isFinite(zone.x_ft) &&
    Number.isFinite(zone.height_ft) &&
    Number.isFinite(zone.top_ft) &&
    Number.isFinite(zone.bottom_ft) &&
    zone.top_ft > zone.bottom_ft;

  let x = 50;
  let y = 50;

  if (available && zone) {
    x = 50 + (zone.x_ft / 0.83) * 32;

    y =
      15 +
      ((zone.top_ft - zone.height_ft) /
        (zone.top_ft - zone.bottom_ft)) *
        70;

    x = Math.max(3, Math.min(97, x));
    y = Math.max(3, Math.min(97, y));
  }

  const result =
    pitch.result_text || '투구 결과 미기록';

  return {
    pitchNumber: pitch.pitch_number ?? 0,
    pitchType:
      pitch.pitch_type_raw ||
      pitch.pitch_type ||
      '구종 미기록',
    speedKm: pitch.speed ?? 0,
    result,
    isStrike:
      result.includes('스트라이크') ||
      result.includes('헛스윙') ||
      result.includes('파울'),
    zoneLocation: { x, y },
    zoneAvailable: available,
    description: result,
  };
}

interface AtBatGroup {
  id: string;
  inning: number;
  half: 'top' | 'bottom';
  batter: string;
  pitcher: string;
  startSeq: number;
  endSeq: number;
  pitches: VisualPitch[];
  lastCount: PitchCount;
  stateAfter: BaseballState;
  resultPlay: ApiPlay | null;
}

function createGroup(
  play: ApiPlay,
  id: string
): AtBatGroup {
  return {
    id,
    inning: play.inning,
    half: play.half,
    batter: play.batter || '타자 미기록',
    pitcher: play.pitcher || '투수 미기록',
    startSeq: play.seq,
    endSeq: play.seq,
    pitches: [],
    lastCount: {
      balls: 0,
      strikes: 0,
    },
    stateAfter:
      play.state_after ||
      play.state_before ||
      emptyState(),
    resultPlay: null,
  };
}

function sameInning(
  group: AtBatGroup,
  play: ApiPlay
): boolean {
  return (
    group.inning === play.inning &&
    group.half === play.half
  );
}

function sameBatter(
  group: AtBatGroup,
  play: ApiPlay
): boolean {
  return (
    !play.batter ||
    group.batter === '타자 미기록' ||
    group.batter === play.batter
  );
}

function toRealAtBat(
  group: AtBatGroup,
  game: GameRecord
): RealAtBat {
  const pitches = group.pitches;
  const lastPitch = pitches[pitches.length - 1];

  const fallbackPitch: VisualPitch = {
    pitchNumber: 0,
    pitchType: '투구 미기록',
    speedKm: 0,
    result: '투구 데이터 없음',
    isStrike: false,
    zoneLocation: { x: 50, y: 50 },
    zoneAvailable: false,
    description: '투구 데이터가 제공되지 않았어요.',
  };

  const outcome =
    group.resultPlay?.description ||
    (lastPitch
      ? `${lastPitch.pitchNumber}구 ${lastPitch.result}`
      : '타석 결과 미기록');

  const awayBatting = group.half === 'top';

  return {
    id: group.id,
    inning: group.inning,
    half: group.half,
    stateAfter: group.stateAfter,
    startSeq: group.startSeq,
    endSeq: group.endSeq,

    batterName: group.batter,
    batterPosition: '',
    batterTeam: awayBatting
      ? game.away
      : game.home,

    pitcherName: group.pitcher,
    pitcherTeam: awayBatting
      ? game.home
      : game.away,

    resultText: outcome,
    resultBadge: `→ ${outcome}`,

    pitchCountText:
      pitches.length > 0
        ? `${pitches.length}구`
        : '투구 미기록',

    pitchesCount: pitches.length,
    balls: group.lastCount.balls,
    strikes: group.lastCount.strikes,
    outs: group.stateAfter.outs,

    currentPitch: lastPitch || fallbackPitch,
    pitchesHistory: pitches,

    // AI 해설 API 연동 전: 가상 해설을 넣지 않음
    aiExplanation: {
      summary: '',
      keyTerms: [],
      evidenceSources: [],
    },
  };
}

function groupAtBats(
  plays: ApiPlay[],
  game: GameRecord
): RealAtBat[] {
  const sorted = [...plays].sort(
    (a, b) => a.seq - b.seq
  );

  const groups: AtBatGroup[] = [];
  let current: AtBatGroup | null = null;

  for (const play of sorted) {
    const eventType = play.event_type;

    if (eventType === 'pitch' && play.pitch) {
      const paId =
        play.pitch.plate_appearance_id ||
        `${game.game_id}:pa:seq:${play.seq}`;

      if (
        !current ||
        current.id !== paId ||
        !sameInning(current, play) ||
        current.resultPlay !== null
      ) {
        current = createGroup(play, paId);
        groups.push(current);
      }

      current.pitches.push(toPitchDetail(play.pitch));

      if (play.pitch.count_after) {
        current.lastCount = play.pitch.count_after;
      }

      current.endSeq = play.seq;

      if (play.state_after) {
        current.stateAfter = play.state_after;
      }

      if (play.batter) current.batter = play.batter;
      if (play.pitcher) current.pitcher = play.pitcher;

      continue;
    }

    if (AT_BAT_RESULT_EVENTS.has(eventType)) {
      const canAttach =
        current !== null &&
        current.resultPlay === null &&
        sameInning(current, play) &&
        sameBatter(current, play);

      if (!canAttach) {
        current = createGroup(
          play,
          `${game.game_id}:result:${play.seq}`
        );
        groups.push(current);
      }

      current!.resultPlay = play;
      current!.endSeq = play.seq;

      if (play.state_after) {
        current!.stateAfter = play.state_after;
      }

      if (play.batter) current!.batter = play.batter;
      if (play.pitcher) current!.pitcher = play.pitcher;

      continue;
    }

    if (FOLLOW_UP_EVENTS.has(eventType)) {
      if (
        current &&
        current.resultPlay !== null &&
        sameInning(current, play)
      ) {
        current.endSeq = play.seq;

        if (play.state_after) {
          current.stateAfter = play.state_after;
        }
      }

      continue;
    }

    // 마운드 방문 등 기타 이벤트로
    // 독립적인 타석을 생성하지 않음
  }

  return groups
    .filter(
      (group) =>
        group.resultPlay !== null ||
        group.pitches.length > 0
    )
    .map((group) => toRealAtBat(group, game));
}

export async function fetchGameScreen(
  gameId: string
): Promise<GameScreenData> {
  const encodedId = encodeURIComponent(gameId);

  const [game, response] = await Promise.all([
    requestJson<GameRecord>(
      `/games/${encodedId}`
    ),
    requestJson<PlaysResponse>(
      `/games/${encodedId}/plays?pitch=true`
    ),
  ]);

  return {
    game,
    atBats: groupAtBats(response.plays, game),
  };
}

export function makeGameSummary(
  game: GameRecord,
  atBat: RealAtBat
): CurrentGameSummary {
  const state = atBat.stateAfter;

  return {
    homeTeam: game.home,
    awayTeam: game.away,

    homeScore: state.score.home,
    awayScore: state.score.away,

    inning: `${atBat.inning}회${
      atBat.half === 'top' ? '초' : '말'
    }`,

    outsCount: state.outs,

    runners: {
      first: Boolean(state.runners['1']),
      second: Boolean(state.runners['2']),
      third: Boolean(state.runners['3']),
    },

    date: game.game_date
      .slice(5)
      .replace('-', '/'),

    stadium: '',

    balls: atBat.balls,
    strikes: atBat.strikes,
  };
}
