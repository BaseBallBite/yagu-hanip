import { memo, useEffect, useState } from 'react';
import { AlertCircle, BookOpen, ChevronDown, GitCommit, Zap } from 'lucide-react';
import { DICTIONARY_CARDS } from '../../data/mockDictionaryData';
import { HIGHLIGHT_API_BASE } from './highlightApi';
import type { HighlightScene, HighlightVideo } from './highlightApi';

interface Props {
  scene: HighlightScene | null;
  video: HighlightVideo;
  onNavigate?: (path: string) => void;
}
const TAG_NAMES: Record<string, string> = {
  ERROR: '실책', SINGLE: '1루타', DOUBLE: '2루타', TRIPLE: '3루타', HOME_RUN: '홈런',
  WALK: '볼넷', HIT_BY_PITCH: '사구', STRIKEOUT: '삼진', SCORE: '득점',
  ADVANCE: '주자 진루', ADVANCE_ON_PLAY: '타구에 따른 진루',
};

function extractEventCardIds(data: unknown): string[] {
  if (typeof data === 'string') return [data];
  if (Array.isArray(data)) return data.flatMap(extractEventCardIds);
  if (!data || typeof data !== 'object') return [];
  const o = data as Record<string, unknown>;
  for (const key of ['cards', 'items', 'results', 'matches', 'card_ids', 'ids']) {
    const value = o[key];
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return Object.keys(value).filter(id => DICTIONARY_CARDS[id]);
    }
    if (Array.isArray(value)) return extractEventCardIds(value);
  }
  const id = o.id ?? o.card_id;
  return typeof id === 'string' ? [id] : [];
}
function EventTags({ tags, onNavigate }: { tags?: string[]; onNavigate?: (path: string) => void }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [choices, setChoices] = useState<{ tag: string; ids: string[] } | null>(null);
  async function openTag(tag: string) {
    setError(''); setChoices(null); setBusy(tag);
    try {
      const response = await fetch(`${HIGHLIGHT_API_BASE}/dict/events/${encodeURIComponent(tag)}`);
      if (!response.ok) throw new Error(`용어 조회 실패 (HTTP ${response.status})`);
      const ids = extractEventCardIds(await response.json()).filter(id => DICTIONARY_CARDS[id]);
      if (!ids.length) { setError('연결되는 사전 카드가 없어요.'); return; }
      if (ids.length === 1) {
        sessionStorage.setItem('yagu_dictionary_target', ids[0]);
        onNavigate?.('/dictionary');
      } else setChoices({ tag, ids });
    } catch (e) { setError(e instanceof Error ? e.message : '사전 연결에 실패했어요.'); }
    finally { setBusy(null); }
  }
  if (!tags?.length) return null; // Game DB is optional. Scenes remain available without tags.
  return <div className="mt-2 flex flex-wrap items-center gap-1.5">
    {tags.map(tag => <button key={tag} type="button" onClick={() => void openTag(tag)} disabled={busy === tag} title={`${TAG_NAMES[tag] ?? tag} 야구사전 열기`} className="inline-flex items-center gap-1 rounded-lg border border-purple-200 bg-white px-2 py-1 text-[11px] font-bold text-purple-700 hover:bg-purple-50 disabled:opacity-50"><BookOpen size={12}/>{TAG_NAMES[tag] ?? tag}</button>)}
    {error && <p role="status" className="w-full text-xs text-amber-700">{error}</p>}
    {choices && <div className="w-full rounded-lg border border-purple-100 p-2 text-xs"><p className="mb-1 font-bold">{TAG_NAMES[choices.tag] ?? choices.tag} 관련 용어</p><div className="flex flex-wrap gap-1">{choices.ids.map(id => <button type="button" key={id} className="rounded-md bg-purple-100 px-2 py-1 text-purple-800" onClick={() => { sessionStorage.setItem('yagu_dictionary_target', id); onNavigate?.('/dictionary'); }}>{DICTIONARY_CARDS[id]?.title ?? id}</button>)}</div></div>}
  </div>;
}
function Bases({ bases }: { bases?: [boolean, boolean, boolean] }) {
  if (!bases) return null;
  return <div className="flex items-center gap-2" aria-label={`주자 ${bases.map((on,i) => on ? `${i+1}루` : '').filter(Boolean).join(', ') || '없음'}`}>
    <span className="text-xs font-bold text-gray-500">주자</span>
    {[0,1,2].map(i => <span key={i} title={`${i+1}루 ${bases[i] ? '주자 있음' : '주자 없음'}`} className={`flex h-6 w-6 rotate-45 items-center justify-center rounded-[3px] border ${bases[i] ? 'border-purple-600 bg-purple-500' : 'border-gray-300 bg-white'}`}><span className={`-rotate-45 text-[9px] font-black ${bases[i] ? 'text-white' : 'text-gray-500'}`}>{i+1}</span></span>)}
  </div>;
}
export const HighlightDetailPanel = memo(function HighlightDetailPanel({ scene, video, onNavigate }: Props) {
  const [showResult, setShowResult] = useState(false);
  useEffect(() => { setShowResult(false); }, [scene?.start, scene?.end]);
  if (!scene || scene.status === '확인 불가') return <div className="mt-5 rounded-2xl border border-gray-200 bg-gray-50 p-5 text-center text-sm text-gray-500">이 장면은 경기 기록과 연결하지 못했어요. 영상은 계속 시청할 수 있어요.</div>;
  const state = scene.situation;
  const runnerReasons = (scene.restore ?? []).filter(line => /^[123]루\s*주자/.test(line));
  const inningScores = (scene.restore ?? []).filter(line => line.startsWith('이번 이닝 앞선 득점'));
  const estimated = scene.status === '추정';
  return <div className={`mt-5 space-y-4 rounded-2xl border p-4 sm:p-5 ${estimated ? 'border-amber-200 bg-amber-50/60' : 'border-purple-100 bg-white'}`}>
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex flex-wrap items-center gap-2"><span className="text-sm font-black text-gray-900">{scene.inning}회{scene.half} · {state?.outs ?? '-'}아웃</span><span className={`rounded-full px-2 py-0.5 text-[11px] font-extrabold ${estimated ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>{estimated ? '추정' : '확인됨'}</span></div>
      {state && <span className="rounded-lg bg-purple-100 px-3 py-1 text-sm font-black text-purple-900">{video.away} {state.score_away} : {state.score_home} {video.home}</span>}
    </div>
    {estimated && <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs font-semibold leading-relaxed text-amber-800"><AlertCircle size={14} className="mr-1 inline"/>전광판이 확인되지 않아 앞 장면을 기준으로 추정한 정보입니다. 실제와 다를 수 있어요.</p>}
    <Bases bases={state?.bases}/>
    <div className="rounded-xl bg-slate-50 p-3"><span className="text-xs font-bold text-gray-500">현재 타자</span><p className="mt-1 text-base font-black text-gray-900">{scene.batter || '타자 정보 없음'}</p></div>
    {scene.prev_play && <div className="rounded-xl border border-purple-100 bg-purple-50 p-3"><h3 className="flex items-center gap-1 text-xs font-extrabold text-purple-800"><Zap size={15}/> 방금</h3><p className="mt-1 text-sm font-bold leading-relaxed text-gray-900">{scene.prev_play}</p><EventTags tags={scene.prev_type_tags} onNavigate={onNavigate}/></div>}
    {(runnerReasons.length > 0 || inningScores.length > 0) && <div className="rounded-xl border border-gray-200 bg-white p-4"><h3 className="mb-2 flex items-center gap-2 text-sm font-extrabold text-gray-800"><GitCommit size={16} className="text-purple-600"/> 이 장면까지 어떻게 왔나요?</h3><div className="space-y-2">{runnerReasons.map((line,i) => <p key={`r-${i}`} className="rounded-lg bg-gray-50 px-3 py-2 text-xs font-semibold text-gray-700">{line}</p>)}{inningScores.map((line,i) => <p key={`s-${i}`} className="rounded-lg bg-purple-50 px-3 py-2 text-xs font-bold text-purple-900">{line}</p>)}</div></div>}
    {scene.result && <div className="rounded-xl border border-purple-200 bg-purple-50/70 p-3"><button type="button" aria-expanded={showResult} onClick={() => setShowResult(v => !v)} className="flex w-full items-center justify-between text-left text-sm font-extrabold text-purple-800">{showResult ? '결과 접기' : '▶ 결과 보기'}<ChevronDown size={17} className={showResult ? 'rotate-180' : ''}/></button>{showResult && <div className="mt-3 border-t border-purple-200 pt-3"><p className="text-sm font-bold leading-relaxed text-gray-900">{scene.result}</p><EventTags tags={scene.result_type_tags} onNavigate={onNavigate}/></div>}</div>}
  </div>;
});
