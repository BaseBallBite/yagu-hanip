import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { AlertCircle, BookOpen, LoaderCircle, Send } from 'lucide-react';
import { requestExplanation } from '../../data/explanationApi';
import type { ExplanationResponse, VerifiedSentence } from '../../data/explanationApi';

interface Props {
  gameId: string;
  playId: string | null;
  batter: string;
  onNavigate?: (path: string) => void;
}
function stringifyEvidence(evidence: unknown): string[] {
  if (typeof evidence === 'string') return [evidence];
  if (Array.isArray(evidence)) return evidence.flatMap(stringifyEvidence);
  if (evidence && typeof evidence === 'object') {
    return Object.entries(evidence).flatMap(([key, value]) => {
      const detail = stringifyEvidence(value);
      return detail.length ? detail.map(item => `${key}: ${item}`) : [];
    });
  }
  return [];
}
function Evidence({ sentence, onNavigate }: { sentence: VerifiedSentence; onNavigate?: (path: string) => void }) {
  const content = stringifyEvidence(sentence.cited_text);
  const ids = Array.isArray(sentence.cited_ids) ? sentence.cited_ids : [];
  if (!content.length && !ids.length) return null;
  return <details className="mt-2 rounded-xl border border-purple-100 bg-white p-3 text-xs text-gray-600">
    <summary className="cursor-pointer font-bold text-purple-700">근거 보기</summary>
    {content.map((line,i) => <p key={i} className="mt-2 whitespace-pre-wrap break-words leading-relaxed">{line}</p>)}
    {ids.length > 0 && <div className="mt-2 flex flex-wrap gap-2">{ids.map((id,i) => {
      const term = typeof id === 'string' && id.startsWith('term.') ? id : null;
      return term ? <button type="button" key={`${id}-${i}`} onClick={() => { sessionStorage.setItem('yagu_dictionary_target', term); onNavigate?.('/dictionary'); }} className="rounded-lg border border-purple-200 bg-purple-50 px-2 py-1 font-bold text-purple-700"><BookOpen className="mr-1 inline h-3 w-3"/>{term === 'term.error' ? '실책' : term === 'term.infield_hit' ? '내야안타' : term.slice(5)}</button> : <span key={`${id}-${i}`} className="rounded-md bg-slate-50 px-2 py-1 text-slate-500">{String(id)}</span>;
    })}</div>}
  </details>;
}
export function VerifiedExplanation({ gameId, playId, batter, onNavigate }: Props) {
  const [question,setQuestion] = useState('이 타석에서는 무슨 일이 일어났나요?');
  const [result,setResult] = useState<ExplanationResponse | null>(null);
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => { setResult(null); setError(''); setLoading(false); abortRef.current?.abort(); return () => abortRef.current?.abort(); }, [gameId,playId]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    const q=question.trim();
    if (!playId) { setError('이 타석의 실제 결과 플레이 ID가 없어 해설을 요청할 수 없어요.'); return; }
    if (!q) { setError('질문을 입력해 주세요.'); return; }
    abortRef.current?.abort(); const controller = new AbortController(); abortRef.current = controller;
    setLoading(true); setResult(null); setError('');
    try { const response = await requestExplanation(gameId,playId,q,controller.signal); if (!controller.signal.aborted) setResult(response); }
    catch(e) { if(!controller.signal.aborted) setError(e instanceof Error ? e.message : '해설을 불러오지 못했어요.'); }
    finally { if(!controller.signal.aborted) setLoading(false); }
  }
  return <section className="mt-4 rounded-2xl border border-purple-200 bg-purple-50/70 p-4" aria-label="AI 경기 해설">
    <h3 className="text-sm font-black text-purple-900">한입만! 경기 해설</h3>
    <p className="mt-1 text-xs text-purple-700">선택한 타자: {batter} · 경기 기록을 근거로 검증한 해설만 표시합니다.</p>
    <form onSubmit={submit} className="mt-3 space-y-2">
      <label className="block text-xs font-bold text-slate-700" htmlFor="game-explanation-question">궁금한 점을 물어보세요</label>
      <textarea id="game-explanation-question" maxLength={300} rows={2} value={question} onChange={e=>setQuestion(e.target.value)} className="w-full resize-y rounded-xl border border-purple-200 bg-white p-3 text-sm text-gray-900 outline-none focus:border-purple-500" placeholder="이 타석에서 왜 득점이 났나요?"/>
      <div className="flex items-center justify-between gap-2"><span className="text-[11px] text-gray-500">{question.length}/300자</span><button type="submit" disabled={loading || !playId || !question.trim()} className="flex items-center gap-2 rounded-xl bg-purple-700 px-4 py-2 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50">{loading ? <LoaderCircle size={15} className="animate-spin"/> : <Send size={15}/>} {loading ? '검증된 해설 생성 중…' : '질문하기'}</button></div>
    </form>
    {!playId && <p className="mt-3 text-xs font-semibold text-amber-700">이 타석에는 결과 플레이 기록이 없어요. 왼쪽 타석 목록에서 안타·아웃·볼넷 등 결과가 있는 타석을 선택해 주세요.</p>}
    {error && <div role="alert" className="mt-3 flex items-start gap-2 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700"><AlertCircle size={15} className="shrink-0"/>{error}</div>}
    {result && <div className="mt-4 space-y-3" aria-live="polite">
      <h4 className="text-xs font-extrabold text-purple-800">검증된 AI 해설</h4>
      {result.sentences?.length ? result.sentences.map((sentence,i) => <div key={i} className="rounded-xl border border-purple-100 bg-white p-3"><p className="whitespace-pre-wrap text-sm font-medium leading-relaxed text-gray-900">{sentence.text}</p><Evidence sentence={sentence} onNavigate={onNavigate}/></div>) : <p className="rounded-xl bg-white p-3 text-sm text-gray-600">검증을 통과한 해설 문장이 없어요. 다른 질문을 입력해 주세요.</p>}
      {typeof result.dropped_count === 'number' && result.dropped_count > 0 && <p className="text-xs text-gray-500">검증에서 제외된 문장 {result.dropped_count}개는 표시하지 않았어요.</p>}
    </div>}
  </section>;
}
