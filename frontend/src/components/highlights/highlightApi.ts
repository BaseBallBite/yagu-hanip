/** B12: the video is streamed by YouTube; only the scene annotations come from our API. */
export const HIGHLIGHT_API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export type HighlightStatus = '확정' | '추정' | '확인 불가';
export interface HighlightVideo {
  video_id: string;
  game_id: string;
  game_date: string;
  away: string;
  home: string;
  scene_count: number;
  duration_sec: number;
}
export interface HighlightScene {
  start: number;
  end: number;
  status: HighlightStatus;
  confidence?: string;
  inning?: number;
  half?: '초' | '말';
  batter?: string | null;
  situation?: {
    outs: number;
    bases: [boolean, boolean, boolean];
    score_away: number;
    score_home: number;
  };
  prev_play?: string | null;
  result?: string | null;
  restore?: string[];
  play_id?: string | null;
  prev_play_id?: string | null;
  play_ids?: string[];
  prev_type_tags?: string[];
  result_type_tags?: string[];
}
export interface HighlightScenesResponse extends HighlightVideo {
  count: number;
  scenes: HighlightScene[];
}
export async function getHighlights(signal?: AbortSignal): Promise<HighlightVideo[]> {
  const res = await fetch(`${HIGHLIGHT_API_BASE}/highlights`, { signal });
  if (!res.ok) throw new Error(`하이라이트 목록 요청 실패 (HTTP ${res.status})`);
  const body = await res.json();
  if (!Array.isArray(body.highlights)) throw new Error('영상 목록 응답 형식이 올바르지 않습니다.');
  return body.highlights;
}
export async function getHighlightScenes(videoId: string, signal?: AbortSignal): Promise<HighlightScenesResponse> {
  const res = await fetch(`${HIGHLIGHT_API_BASE}/highlights/${encodeURIComponent(videoId)}/scenes`, { signal });
  if (!res.ok) throw new Error(`장면 표 요청 실패 (HTTP ${res.status})`);
  const body = await res.json();
  if (!Array.isArray(body.scenes)) throw new Error('장면 표 응답 형식이 올바르지 않습니다.');
  return body;
}
export function sceneAtTime(scenes: HighlightScene[], time: number): number {
  // End is exclusive: an exact boundary belongs to the following scene.
  let lo = 0, hi = scenes.length - 1;
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    const scene = scenes[mid];
    if (time < scene.start) hi = mid - 1;
    else if (time >= scene.end) lo = mid + 1;
    else return mid;
  }
  return -1;
}
export function formatHighlightTime(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
