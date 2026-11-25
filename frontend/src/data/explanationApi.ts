const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface VerifiedSentence {
  text: string;
  cited_ids?: string[] | null;
  cited_text?: unknown;
  check?: unknown;
  p_support?: number | null;
}
export interface ExplanationResponse {
  mode?: string;
  source?: string;
  game_id: string;
  play_id: string;
  question: string;
  sentences: VerifiedSentence[];
  dropped_count?: number;
  chip_id?: string;
  chip_label?: string;
  verifier?: unknown;
  generation?: unknown;
}
const ERROR_MESSAGES: Record<number,string> = {
  404: '선택한 플레이를 찾을 수 없거나 해설 대상이 아니에요.',
  422: '이 장면에서는 쓸 수 없는 질문이에요. 다른 칩을 눌러 주세요.',
  502: '해설 생성 또는 검증에 실패했어요. 검증되지 않은 답변은 표시하지 않습니다.',
  503: '해설 API가 비활성화되어 있거나 DB·Gemini·KLUE 실행 환경이 준비되지 않았어요.',
};
export interface QuestionChip { id: string; label: string; }
export interface QuestionChipsResponse {
  game_id: string;
  play_id: string;
  tag: string;
  entry: QuestionChip;
  follow_ups: QuestionChip[];
}

/** 플레이에 보여줄 질문 칩: 입구 q.why(한입만) + 「한입 더」 후속 칩 1~2개. */
export async function fetchQuestionChips(gameId: string, playId: string, signal?: AbortSignal): Promise<QuestionChipsResponse> {
  const params = new URLSearchParams({ game_id: gameId, play_id: playId });
  const response = await fetch(`${API_BASE}/explanations/chips?${params}`, { signal });
  if (!response.ok) throw new Error(response.status === 404 ? '이 장면의 질문 칩을 찾을 수 없어요.' : `질문 칩을 불러오지 못했어요. (HTTP ${response.status})`);
  const body: QuestionChipsResponse = await response.json();
  if (!body.entry || !Array.isArray(body.follow_ups)) throw new Error('질문 칩 응답 형식이 올바르지 않아요.');
  return body;
}

/** 칩 ID로 해설 요청. 자유 입력은 받지 않는다(질문 문장은 서버가 칩 ID로 고정). */
export async function requestExplanation(gameId: string, playId: string, chipId: string, signal?: AbortSignal): Promise<ExplanationResponse> {
  const response = await fetch(`${API_BASE}/explanations/generate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId, play_id: playId, chip_id: chipId }), signal,
  });
  if(!response.ok) throw new Error(ERROR_MESSAGES[response.status] || `해설 요청에 실패했어요. (HTTP ${response.status})`);
  const body: ExplanationResponse = await response.json();
  if (!Array.isArray(body.sentences) || body.game_id !== gameId || body.play_id !== playId) throw new Error('해설 API 응답의 대상 플레이 또는 문장 구조가 올바르지 않아요.');
  return body;
}
