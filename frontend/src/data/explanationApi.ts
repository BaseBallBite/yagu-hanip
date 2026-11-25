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
  verifier?: unknown;
  generation?: unknown;
}
const ERROR_MESSAGES: Record<number,string> = {
  404: '선택한 플레이를 찾을 수 없거나 해설 대상이 아니에요.',
  422: '질문 또는 플레이 정보가 올바르지 않아요. 선택한 타자의 플레이에 대해 질문해 주세요.',
  502: '해설 생성 또는 검증에 실패했어요. 검증되지 않은 답변은 표시하지 않습니다.',
  503: '해설 API가 비활성화되어 있거나 DB·Gemini·KLUE 실행 환경이 준비되지 않았어요.',
};
export async function requestExplanation(gameId: string, playId: string, question: string, signal?: AbortSignal): Promise<ExplanationResponse> {
  const response = await fetch(`${API_BASE}/explanations/generate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId, play_id: playId, question }), signal,
  });
  if(!response.ok) throw new Error(ERROR_MESSAGES[response.status] || `해설 요청에 실패했어요. (HTTP ${response.status})`);
  const body: ExplanationResponse = await response.json();
  if (!Array.isArray(body.sentences) || body.game_id !== gameId || body.play_id !== playId) throw new Error('해설 API 응답의 대상 플레이 또는 문장 구조가 올바르지 않아요.');
  return body;
}
