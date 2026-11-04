/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface DictionaryCategory {
  id: string;
  name: string;
  terms: string[];
}

export interface RAGSource {
  title: string;
  sourceType: string;
  referenceUrl?: string;
}

export interface TermFlowStep {
  stepNumber: number;
  label: string;
  detail: string;
}

export interface TermDetail {
  name: string;
  englishName: string;
  category: string;
  oneLineSummary: string;
  beginnerExplanation: string;
  gameFlow: string[];
  relatedTerms: string[];
  sources: RAGSource[];
  defaultFollowUpQuestion?: string;
  defaultFollowUpAnswer?: string;
}

export const DICTIONARY_CATEGORIES: DictionaryCategory[] = [
  {
    id: 'basic',
    name: '기본',
    terms: [
      'ABS',
      '볼',
      '스트라이크',
      '볼카운트',
      '아웃',
      '이닝',
      '삼진',
      '몸에 맞는 볼',
      '헛스윙',
      '파울',
      '피치클락',
    ],
  },
  {
    id: 'rules',
    name: '규칙',
    terms: [
      '인필드 플라이',
      '낫아웃',
      '보크',
      '포스 플레이',
      '볼넷',
      '스트라이크 존',
      '태그',
      '폭투',
      '포일',
      '견제',
    ],
  },
  {
    id: 'batting',
    name: '타격',
    terms: [
      '안타',
      '2루타',
      '3루타',
      '홈런',
      '땅볼',
      '플라이',
      '라인드라이브',
      '병살',
      '희생플라이',
      '실책',
    ],
  },
];

// Rich predefined details for terms
export const MOCK_TERM_DETAILS: Record<string, TermDetail> = {
  '병살': {
    name: '병살',
    englishName: 'Double Play',
    category: '타격',
    oneLineSummary: '하나의 플레이로 두 명의 주자가 아웃되는 상황이에요.',
    beginnerExplanation: `예를 들어 1루에 주자가 있는 상황에서 타자가 땅볼을 치면, 수비수가 먼저 2루에서 주자를 아웃시키고 이어서 1루에서 타자까지 아웃시킬 수 있어요.\n\n이렇게 한 번의 플레이에서 두 명이 아웃되면 '병살'이라고 해요.`,
    gameFlow: [
      '1루 주자 있음',
      '타자 땅볼 타격',
      '2루에서 주자 아웃',
      '1루에서 타자 아웃',
      '병살 완성',
    ],
    relatedTerms: ['#포스아웃', '#땅볼', '#주자', '#아웃'],
    sources: [
      { title: 'KBO 공식 야구 규칙 제5.09조 (아웃의 성립 및 병살타)', sourceType: '공식 규정' },
      { title: 'KBO 야구 용어 사전 2026 개정판', sourceType: '공식 용어집' },
    ],
    defaultFollowUpQuestion: '병살은 언제 가능한가요?',
    defaultFollowUpAnswer: '병살은 주로 주자가 베이스에 있고 아웃카운트가 0아웃 또는 1아웃일 때 성립해요. 이미 2아웃인 상황에서는 한 명만 아웃되어도 이닝이 끝나기 때문에 병살이 나오지 않습니다!',
  },
  '낫아웃': {
    name: '낫아웃',
    englishName: 'Uncaught Third Strike',
    category: '규칙',
    oneLineSummary: '3번째 스트라이크를 포수가 바로 잡지 못해 타자가 1루로 뛸 수 있는 특별한 규칙이에요.',
    beginnerExplanation: `스트라이크가 3개가 되면 보통 삼진 아웃이지만, 포수가 그 3번째 공을 땅에 떨어뜨리거나 놓치면 타자는 아직 완전히 아웃되지 않은 상태가 돼요.\n\n이때 타자가 1루까지 전력 질주해 포수의 송구보다 먼저 밟으면 출루할 수 있어요!`,
    gameFlow: [
      '2스트라이크 상황',
      '3구째 헛스윙 또는 스트라이크',
      '포수가 공을 놓침 (원바운드)',
      '타자가 1루로 전력 질주',
      '포수 송구 전 1루 세이프 시 출루 성공',
    ],
    relatedTerms: ['#삼진', '#포수', '#출루', '#스트라이크'],
    sources: [
      { title: 'KBO 공식 야구 규칙 제5.05조 (타자가 주자가 되는 경우)', sourceType: '공식 규정' },
      { title: '야구 규칙 해설집 - 스트라이크 삼진 낫아웃 조항', sourceType: '해설서' },
    ],
    defaultFollowUpQuestion: '1루에 주자가 있어도 낫아웃이 가능한가요?',
    defaultFollowUpAnswer: '1루에 주자가 없을 때는 언제든 가능해요! 단, 1루에 이미 주자가 있다면 2아웃일 때만 낫아웃이 인정됩니다 (0아웃, 1아웃에 1루 주자가 있으면 고의로 떨어뜨려 병살을 노리는 것을 막기 위함입니다).',
  },
  '보크': {
    name: '보크',
    englishName: 'Balk',
    category: '규칙',
    oneLineSummary: '투수가 주자를 속이려고 부정하거나 부자연스러운 동작을 했을 때 선언되는 페널티예요.',
    beginnerExplanation: `주자가 루상에 있을 때, 투수가 타자에게 던질 것처럼 폼을 잡다가 갑자기 멈추거나, 베이스로 발을 내딛지 않고 주자를 속여 던지는 부정 동작을 하면 심판이 '보크'를 선언해요.\n\n보크가 선언되면 베이스에 있던 모든 주자는 안전하게 한 베이스씩 진루할 수 있어요!`,
    gameFlow: [
      '주자가 있는 상황',
      '투수의 불규칙하거나 멈추는 투구 동작',
      '심판의 보크 선언 (휘슬/콜)',
      '모든 주자 1베이스씩 안전 진루',
    ],
    relatedTerms: ['#견제', '#주자', '#진루', '#투구동작'],
    sources: [
      { title: 'KBO 공식 야구 규칙 제6.02조 (투수의 부정 행위 및 보크)', sourceType: '공식 규정' },
      { title: 'KBO 심판위원회 투구 판정 가이드라인', sourceType: '심판 지침서' },
    ],
    defaultFollowUpQuestion: '보크가 나오면 타자는 어떻게 되나요?',
    defaultFollowUpAnswer: '보크는 주로 루상의 주자를 보호하기 위한 규칙이에요. 공이 실제로 던져지지 않았다면 볼카운트는 그대로 유지되고, 주자들만 한 베이스씩 앞으로 이동합니다.',
  },
  '인필드 플라이': {
    name: '인필드 플라이',
    englishName: 'Infield Fly',
    category: '규칙',
    oneLineSummary: '내야에 뜬 평범한 뜬공을 수비수가 고의로 떨어뜨려 병살을 만드는 것을 막는 보호 규칙이에요.',
    beginnerExplanation: `0아웃이나 1아웃에 주자가 1·2루 또는 만루일 때, 타자가 내야수 머리 위로 높게 뜬공을 치면 심판이 공이 잡히기 전 미리 '인필드 플라이'를 선언해요.\n\n이 콜이 나오면 수비수가 공을 놓치거나 떨어뜨려도 타자는 무조건 아웃 처리되어 주자들이 억울하게 아웃되는 걸 막아줘요.`,
    gameFlow: [
      '무사 또는 1사 주자 1·2루/만루',
      '타자가 내야 높이 뜬공 타격',
      '심판이 "인필드 플라이" 즉시 선언',
      '수비 포구 여부와 상관없이 타자 자동 아웃',
      '주자는 무리해서 뛰지 않아도 안전',
    ],
    relatedTerms: ['#플라이', '#포스아웃', '#내야수', '#만루'],
    sources: [
      { title: 'KBO 공식 야구 규칙 제5.09조 (인필드 플라이 규정)', sourceType: '공식 규정' },
      { title: 'KBO 규칙 용어 사전', sourceType: '공식 용어집' },
    ],
    defaultFollowUpQuestion: '인필드 플라이 상황에서 주자가 달려도 되나요?',
    defaultFollowUpAnswer: '주자는 자신의 판단에 따라 뛸 수도 있어요! 단, 수비수가 공을 정상 포구했다면 원래 베이스를 다시 터치(리터치)하고 뛰어야 하며, 잡지 못하고 떨어뜨렸다면 리터치 없이 다음 루로 뛸 수 있습니다.',
  },
  '도루': {
    name: '도루',
    englishName: 'Stolen Base',
    category: '규칙',
    oneLineSummary: '투수가 타자에게 공을 던지는 틈을 타 주자가 다음 베이스로 빠르게 달려서 훔치는 플레이예요.',
    beginnerExplanation: `타자가 안타를 치지 않아도, 투수가 와인드업이나 세트포지션에서 공을 던지는 찰나의 순간에 주자가 다음 베이스로 전력 질주해 세이프가 되면 '도루 성공'이 돼요.\n\n보통 1루에서 2루로 뛰는 2루 도루가 가장 많이 발생해요!`,
    gameFlow: [
      '주자가 베이스에서 리드(거리 확보)',
      '투수가 타자를 향해 투구 시작',
      '주자가 다음 루로 전력 질주',
      '포수의 빠른 2루 송구',
      '태그보다 주자의 슬라이딩이 빨라 세이프',
    ],
    relatedTerms: ['#세이프', '#포수송구', '#주루', '#태그'],
    sources: [
      { title: 'KBO 공식 야구 규칙 제9.07조 (도루)', sourceType: '공식 규정' },
      { title: 'KBO 공식 기록 가이드', sourceType: '기록 규정' },
    ],
    defaultFollowUpQuestion: '도루는 몇 루까지 가능한가요?',
    defaultFollowUpAnswer: '2루 도루, 3루 도루는 물론 홈 플레이트로 파고드는 홈 스틸(홈 도루)도 규칙상 가능해요! 홈 도루는 투수의 타이밍을 완벽하게 뺏어야 해서 매우 드물고 짜릿한 플레이입니다.',
  },
  'ABS': {
    name: 'ABS',
    englishName: 'Automatic Ball-Strike System',
    category: '기본',
    oneLineSummary: '컴퓨터 카메라가 공의 궤적을 추적해 스트라이크/볼을 정확하게 판정하는 자동 투구 판정 시스템(로봇 심판)이에요.',
    beginnerExplanation: `KBO가 세계 최초로 1군 전 경기에 도입한 시스템이에요.\n\n구장에 설치된 여러 대의 정밀 카메라가 투수가 던진 공의 궤적을 3차원으로 추적하고, 타자의 키에 맞춰 정해진 스트라이크 존을 통과했는지를 컴퓨터가 0.1초 만에 판정해 주심의 이어폰으로 음성 전달해줘요.`,
    gameFlow: [
      '투수 투구',
      '구장 추적 카메라가 공 궤적 계산',
      '설정된 스트라이크 존 통과 여부 자동 판별',
      '주심 무전기로 "스트라이크" 또는 "볼" 음성 전달',
      '주심이 최종 판정 선언',
    ],
    relatedTerms: ['#스트라이크존', '#로봇심판', '#판정', '#피치클락'],
    sources: [
      { title: '2026 KBO 자동 투구 판정 시스템(ABS) 운영 지침', sourceType: 'KBO 특별 규정' },
      { title: 'KBO 리그 기술 혁신 백서', sourceType: '공식 보도자료' },
    ],
    defaultFollowUpQuestion: 'ABS 판정에 선수가 항의할 수 있나요?',
    defaultFollowUpAnswer: 'ABS의 스트라이크/볼 판정에 대해서는 선수나 감독이 항의하거나 비디오 판독을 신청할 수 없어요! 기계가 모든 타자에게 동일한 기준으로 엄격하게 판정하기 때문입니다.',
  },
  '피치클락': {
    name: '피치클락',
    englishName: 'Pitch Clock',
    category: '기본',
    oneLineSummary: '경기 시간을 단축하고 박진감을 높이기 위해 투수와 타자의 준비 시간을 제한하는 타이머예요.',
    beginnerExplanation: `투수는 주자가 없을 때 18초, 주자가 있을 때 23초 이내에 반드시 투구 동작을 시작해야 해요.\n\n타자도 타이머가 8초 남을 때까지 타석에 들어서서 칠 준비를 끝내야 하며, 시간을 초과하면 투수에게는 볼 1개, 타자에게는 스트라이크 1개의 페널티가 부과돼요.`,
    gameFlow: [
      '포수의 공 포구 후 타이머 작동 시작',
      '타자는 8초 남을 때까지 타격 준비 완료',
      '투수는 0초가 되기 전 투구 시작',
      '시간 초과 시 심판이 페널티 선언 (볼/스트라이크 추가)',
    ],
    relatedTerms: ['#경기시간', '#투구준비', '#페널티', '#볼카운트'],
    sources: [
      { title: '2026 KBO 리그 스피드업 규정 - 피치클락 세칙', sourceType: '공식 지침' },
      { title: 'KBO 경기 시간 단축 운영 위원회', sourceType: '공식 규정' },
    ],
    defaultFollowUpQuestion: '투수가 견제구를 던지면 피치클락은 어떻게 되나요?',
    defaultFollowUpAnswer: '투수가 주자에게 견제구를 던지거나 투수판에서 발을 빼면 피치클락은 멈추고 다시 리셋돼요! 단, 한 타석당 견제 횟수에도 제한이 있어 무제한으로 시간을 끌 수는 없습니다.',
  },
};

// Fallback generator for other terms
export function getTermDetailOrDefault(termName: string): TermDetail {
  if (MOCK_TERM_DETAILS[termName]) {
    return MOCK_TERM_DETAILS[termName];
  }

  // Find category
  let categoryName = '기본';
  for (const cat of DICTIONARY_CATEGORIES) {
    if (cat.terms.includes(termName)) {
      categoryName = cat.name;
      break;
    }
  }

  return {
    name: termName,
    englishName: `${termName} (Baseball Term)`,
    category: categoryName,
    oneLineSummary: `${termName}은(는) 야구 경기에서 자주 등장하는 핵심 ${categoryName} 용어예요.`,
    beginnerExplanation: `야구 경기를 보다 보면 "${termName}"이라는 말을 자주 듣게 돼요.\n\n이 용어는 경기 중 특정 상황이나 선수의 플레이 결과를 나타내며, 야구 규칙을 이해하는 데 매우 중요한 기본 개념이에요.`,
    gameFlow: [
      '상황 발생',
      `${termName} 조건 충족`,
      '심판 및 공식 기록원 판정',
      '플레이 결과 적용',
    ],
    relatedTerms: ['#야구규칙', '#플레이', '#KBO', '#기초용어'],
    sources: [
      { title: `KBO 공식 야구 규칙서 2026 - ${termName} 편`, sourceType: '공식 규정' },
      { title: '야구한입 RAG 지식 데이터베이스', sourceType: 'AI 지식베이스' },
    ],
    defaultFollowUpQuestion: `${termName} 상황에서 가장 주의할 점은 무엇인가요?`,
    defaultFollowUpAnswer: `${termName}이(가) 발생했을 때는 아웃카운트와 루상의 주자 움직임이 어떻게 바뀌는지 확인하는 것이 가장 중요해요!`,
  };
}
