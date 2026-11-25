import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, BookOpen, LoaderCircle, RotateCcw } from 'lucide-react';
import { fetchQuestionChips, requestExplanation } from '../../data/explanationApi';
import type { ExplanationResponse, QuestionChip, VerifiedSentence } from '../../data/explanationApi';
import { DICTIONARY_CARDS } from '../../data/mockDictionaryData';

interface Props {
  gameId: string;
  playId: string | null;
  batter: string;
  onNavigate?: (path: string) => void;
}
type DictionaryCard = { title?: string };
const CARDS = DICTIONARY_CARDS as Record<string, DictionaryCard>;

/** cited_text([{id, text}])에서 사람이 읽을 근거 문장만 꺼낸다. 사전 카드(규칙·용어)는 칩으로 따로 보여준다. */
function evidenceLines(evidence: unknown): string[] {
  if (!Array.isArray(evidence)) return typeof evidence === 'string' ? [evidence] : [];
  return evidence.flatMap(item => {
    if (typeof item === 'string') return [item];
    if (item && typeof item === 'object') {
      const { id, text } = item as { id?: unknown; text?: unknown };
      if (typeof id === 'string' && CARDS[id]) return [];
      return typeof text === 'string' && text.trim() ? [text] : [];
    }
    return [];
  });
}
function Evidence({ sentence, onNavigate }: { sentence: VerifiedSentence; onNavigate?: (path: string) => void }) {
  const lines = Array.from(new Set(evidenceLines(sentence.cited_text)));
  const ids = Array.isArray(sentence.cited_ids) ? sentence.cited_ids : [];
  const cardIds = Array.from(new Set(ids.filter((id): id is string => typeof id === 'string' && Boolean(CARDS[id]))));
  if (!lines.length && !cardIds.length) return null;
  return <details className="mt-2 rounded-xl border border-purple-100 bg-white p-3 text-xs text-gray-600">
    <summary className="cursor-pointer font-bold text-purple-700">근거 보기</summary>
    {lines.length > 0 && <ul className="mt-2 space-y-1">{lines.map((line,i) => <li key={i} className="flex items-start gap-2 break-words leading-relaxed"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-400"/><span>{line}</span></li>)}</ul>}
    {cardIds.length > 0 && <div className="mt-3 flex flex-wrap items-center gap-2">
      <span className="text-[11px] text-gray-400">관련 용어·규칙</span>
      {cardIds.map(id => <button type="button" key={id} onClick={() => { sessionStorage.setItem('yagu_dictionary_target', id); onNavigate?.('/dictionary'); }} className="rounded-lg border border-purple-200 bg-purple-50 px-2 py-1 font-bold text-purple-700 hover:bg-purple-100"><BookOpen className="mr-1 inline h-3 w-3"/>{CARDS[id]?.title ?? id}</button>)}
    </div>}
  </details>;
}
type Answer = {
  chip: QuestionChip;
  status: 'loading' | 'done' | 'error';
  result?: ExplanationResponse;
  error?: string;
};

const NOT_READY = '준비되지 않은 설명이에요.';

/**
 * A4 질문 칩 흐름: 「한입만」(q.why)으로 기본 해설 → 「한입 더」 후속 칩 1~2개.
 * 후속 칩은 한 번씩만 누를 수 있고, 후속의 후속은 없다. 자유 입력은 받지 않는다.
 */
export function VerifiedExplanation({ gameId, playId, batter, onNavigate }: Props) {
  const [followUps, setFollowUps] = useState<QuestionChip[]>([]);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [chipError, setChipError] = useState('');
  const controllers = useRef<AbortController[]>([]);

  const abortAll = () => { controllers.current.forEach(c => c.abort()); controllers.current = []; };

  const ask = useCallback(async (chip: QuestionChip) => {
    if (!playId) return;
    const controller = new AbortController();
    controllers.current.push(controller);
    setAnswers(prev => {
      const rest = prev.filter(a => a.chip.id !== chip.id);
      const index = prev.findIndex(a => a.chip.id === chip.id);
      const next: Answer = { chip, status: 'loading' };
      if (index < 0) return [...rest, next];
      const copy = [...prev]; copy[index] = next; return copy; // 다시 시도는 같은 자리에서
    });
    try {
      const result = await requestExplanation(gameId, playId, chip.id, controller.signal);
      if (!controller.signal.aborted) setAnswers(prev => prev.map(a => a.chip.id === chip.id ? { chip, status: 'done', result } : a));
    } catch (e) {
      if (!controller.signal.aborted) setAnswers(prev => prev.map(a => a.chip.id === chip.id ? { chip, status: 'error', error: e instanceof Error ? e.message : '해설을 불러오지 못했어요.' } : a));
    }
  }, [gameId, playId]);

  // 장면이 바뀌면 칩을 새로 받고, 입구 칩(한입만)으로 기본 해설을 바로 요청한다.
  useEffect(() => {
    abortAll();
    setAnswers([]); setFollowUps([]); setChipError('');
    if (!playId) return;
    const controller = new AbortController();
    controllers.current.push(controller);
    fetchQuestionChips(gameId, playId, controller.signal)
      .then(chips => {
        if (controller.signal.aborted) return;
        setFollowUps(chips.follow_ups);
        void ask(chips.entry);
      })
      .catch(e => { if (!controller.signal.aborted) setChipError(e instanceof Error ? e.message : '질문 칩을 불러오지 못했어요.'); });
    return abortAll;
  }, [gameId, playId, ask]);

  const busy = answers.some(a => a.status === 'loading');
  const baseDone = answers[0]?.status === 'done';
  const usedIds = new Set(answers.map(a => a.chip.id));

  return <section className="mt-4 rounded-2xl border border-purple-200 bg-purple-50/70 p-4" aria-label="AI 경기 해설">
    <h3 className="text-sm font-black text-purple-900">한입만! 경기 해설</h3>
    <p className="mt-1 text-xs text-purple-700">선택한 타자: {batter} · 경기 기록과 규칙 카드로 검증한 해설만 보여줘요.</p>

    {!playId && <p className="mt-3 text-xs font-semibold text-amber-700">이 타석에는 결과 플레이 기록이 없어요. 안타·아웃·볼넷처럼 결과가 있는 타석을 골라 주세요.</p>}
    {chipError && <div role="alert" className="mt-3 flex items-start gap-2 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700"><AlertCircle size={15} className="shrink-0"/>{chipError}</div>}

    <div className="mt-3 space-y-4" aria-live="polite">
      {answers.map((answer, index) => <div key={answer.chip.id}>
        {index === 0
          ? <p className="text-xs font-bold text-purple-800">한입에 설명해줄게요 🍙</p>
          : <p className="text-xs font-bold text-purple-800">Q. {answer.chip.label}</p>}
        {answer.status === 'loading' && <div className="mt-2 flex items-center gap-2 rounded-xl bg-white p-3 text-xs font-semibold text-purple-700" role="status"><LoaderCircle size={15} className="animate-spin"/>검증된 해설을 만들고 있어요… (20초쯤 걸려요)</div>}
        {answer.status === 'error' && <div role="alert" className="mt-2 rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-700">
          <p className="flex items-start gap-2"><AlertCircle size={15} className="shrink-0"/>{answer.error}</p>
          <button type="button" disabled={busy} onClick={() => void ask(answer.chip)} className="mt-2 flex items-center gap-1 underline disabled:opacity-50"><RotateCcw size={12}/>다시 시도</button>
        </div>}
        {answer.status === 'done' && answer.result && <div className="mt-2 space-y-2">
          {answer.result.sentences?.length
            ? answer.result.sentences.map((sentence, i) => <div key={i} className="rounded-xl border border-purple-100 bg-white p-3"><p className="whitespace-pre-wrap text-sm font-medium leading-relaxed text-gray-900">{sentence.text}</p><Evidence sentence={sentence} onNavigate={onNavigate}/></div>)
            : <p className="rounded-xl bg-white p-3 text-sm text-gray-600">{NOT_READY}</p>}
        </div>}
      </div>)}
    </div>

    {baseDone && followUps.length > 0 && <div className="mt-4 border-t border-purple-100 pt-3">
      <p className="text-xs font-extrabold text-purple-900">한입 더</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {followUps.map(chip => {
          const used = usedIds.has(chip.id);
          return <button type="button" key={chip.id} disabled={used || busy} onClick={() => void ask(chip)} aria-pressed={used}
            className={`rounded-xl border px-3 py-2 text-left text-xs font-bold transition ${used ? 'cursor-default border-gray-200 bg-gray-100 text-gray-400' : 'border-purple-200 bg-white text-purple-800 hover:bg-purple-100 disabled:cursor-wait disabled:opacity-60'}`}>
            {chip.label}
          </button>;
        })}
      </div>
    </div>}
  </section>;
}
