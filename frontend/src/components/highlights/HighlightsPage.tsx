/** B12: real YouTube highlights, precomputed scene records, no online AI calls. */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, Calendar, ChevronDown, Clock, LoaderCircle, Play, Sparkles } from 'lucide-react';
import { HighlightDetailPanel } from './HighlightDetailPanel';
import { YouTubeHighlightPlayer } from './YouTubeHighlightPlayer';
import { formatHighlightTime, getHighlights, getHighlightScenes, sceneAtTime } from './highlightApi';
import type { HighlightVideo, HighlightScenesResponse } from './highlightApi';

const DEMO_VIDEO = 'YQD3hMI2LPo';
const DEMO_IDS = [DEMO_VIDEO, 'FaJDs51xcTU', 'zqPWIKkZLF0'];
const DEMO_MARKS = [
  { t: 435, title: '두산 2사 만루', description: '양의지 몸에 맞는 볼' },
  { t: 480, title: '김민석 동점타', description: '3:3 · 추정 장면' },
  { t: 640, title: 'LG 만루 상황', description: '앞선 주자 출루 이유' },
  { t: 755, title: '이재원 타석', description: '결과 보기로 타석 결과 확인' },
];
export function HighlightsPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const [videos, setVideos] = useState<HighlightVideo[]>([]);
  const sceneCache = useRef<Map<string, HighlightScenesResponse>>(new Map());
  const [selectedId, setSelectedId] = useState(DEMO_VIDEO);
  const [data, setData] = useState<HighlightScenesResponse | null>(null);
  const [listError, setListError] = useState('');
  const [sceneError, setSceneError] = useState('');
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [seekSeconds, setSeekSeconds] = useState<number | null>(null);
  const [seekToken, setSeekToken] = useState(0);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [showAllScenes, setShowAllScenes] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    getHighlights(controller.signal).then(all => {
      setVideos(all.filter(v => DEMO_IDS.includes(v.video_id)).sort((a,b) => DEMO_IDS.indexOf(a.video_id) - DEMO_IDS.indexOf(b.video_id)));
    }).catch(e => { if (!controller.signal.aborted) setListError(e instanceof Error ? e.message : '영상 목록을 불러오지 못했어요.'); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setSceneError('');
    setData(null);
    setActiveIndex(-1);
    setCurrentTime(0);
    setSeekSeconds(null);
    setSeekToken(0);
    setShowAllScenes(false);
    const cached = sceneCache.current.get(selectedId);
    if (cached) { setData(cached); setLoading(false); return () => controller.abort(); }
    getHighlightScenes(selectedId, controller.signal).then(response => {
      if (!controller.signal.aborted) {
        const sorted = { ...response, scenes: [...response.scenes].sort((a,b) => a.start-b.start) };
        sceneCache.current.set(selectedId, sorted);
        setData(sorted);
      }
    }).catch(e => { if (!controller.signal.aborted) setSceneError(e instanceof Error ? e.message : '장면 표를 불러오지 못했어요.'); })
    .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [selectedId]);
  const updateTime = useCallback((t: number) => setCurrentTime(t), []);
  useEffect(() => {
    if (!data) return;
    const index = sceneAtTime(data.scenes, currentTime);
    setActiveIndex(old => old === index ? old : index);
  }, [currentTime, data]);
  const jumpTo = useCallback((time: number) => { setSeekSeconds(time); setSeekToken(v => v + 1); setCurrentTime(time); }, []);
  const activeScene = useMemo(() => activeIndex >= 0 ? data?.scenes[activeIndex] ?? null : null, [data, activeIndex]);
  const videoName = data ? `${data.away} vs ${data.home}` : (videos.find(v => v.video_id === selectedId)?.away ?? '영상');
  return <div className="w-full flex-1 py-6 sm:py-8 animate-fade-in">
    <div className="max-w-[1840px] w-full mx-auto px-3 sm:px-4 lg:px-5 2xl:px-6">
      <div className="mb-6 border-b border-gray-200/70 pb-5">
        <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-purple-100 px-3 py-1 text-xs font-bold text-purple-700"><Sparkles size={14}/> AI 장면 복원</div>
        <h1 className="text-2xl sm:text-3xl font-black text-gray-900">경기 하이라이트</h1>
        <p className="mt-1 text-sm text-gray-500">YouTube 영상과 함께 AI가 경기 기록에서 복원한 장면 상황을 확인해 보세요.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[225px_minmax(0,1fr)] 2xl:grid-cols-[245px_minmax(0,1fr)] gap-4 xl:gap-5 items-start xl:h-[calc(100dvh-235px)] xl:min-h-[450px] xl:overflow-hidden">
        <aside className="min-w-0 space-y-5 xl:h-full xl:min-h-0 xl:overflow-y-auto xl:overscroll-contain xl:pr-1" aria-label="시연 경기와 장면 탐색">
          <section className="rounded-3xl border border-gray-100 bg-white p-5 shadow-lg shadow-purple-950/5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-black text-gray-900"><Calendar size={17} className="text-purple-600"/> 시연 경기</h2>
            {listError && <p role="alert" className="text-xs text-rose-600">{listError}</p>}
            <div className="space-y-2">{videos.map(video => <button type="button" key={video.video_id} onClick={() => setSelectedId(video.video_id)} className={`w-full rounded-xl border p-3 text-left text-sm transition ${selectedId === video.video_id ? 'border-purple-500 bg-purple-50 text-purple-900' : 'border-gray-200 hover:border-purple-300'}`}>
              <span className="block font-bold">{video.away} vs {video.home}</span><span className="text-xs text-gray-500">{video.game_date} · 장면 {video.scene_count}개</span>
            </button>)}</div>
            {!videos.length && !listError && <p className="text-xs text-gray-500">영상 목록을 불러오는 중…</p>}
          </section>
          <section className="rounded-3xl border border-gray-100 bg-white p-5 shadow-lg shadow-purple-950/5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-black text-gray-900"><Clock size={17} className="text-purple-600"/> 장면 이동</h2>
            {selectedId === DEMO_VIDEO && <div className="space-y-2">{DEMO_MARKS.map(mark => <button type="button" key={mark.t} onClick={() => jumpTo(mark.t)} className="flex w-full items-center gap-3 rounded-xl border border-gray-200 p-3 text-left hover:bg-purple-50 hover:border-purple-300">
              <span className="rounded-lg bg-purple-100 px-2 py-1 font-bold text-purple-700 text-xs">{formatHighlightTime(mark.t)}</span>
              <span className="min-w-0"><span className="block text-xs font-extrabold">{mark.title}</span><span className="block text-[11px] text-gray-500">{mark.description}</span></span><Play size={14} className="ml-auto text-purple-500"/>
            </button>)}</div>}
            <button type="button" onClick={() => setShowAllScenes(v => !v)} className="mt-3 flex w-full items-center justify-between rounded-xl border border-gray-200 px-3 py-2 text-xs font-bold text-gray-600 hover:bg-gray-50" aria-expanded={showAllScenes}>전체 장면 구간 {data?.count ?? 0}개 <ChevronDown size={16} className={showAllScenes ? 'rotate-180' : ''}/></button>
            {showAllScenes && <div className="mt-2 max-h-72 space-y-1 overflow-y-auto" aria-label="전체 장면 시작 시간">
              {data?.scenes.map((scene,i) => <button type="button" key={`${scene.start}-${i}`} onClick={() => jumpTo(scene.start + 0.05)} className={`w-full rounded-lg px-3 py-2 text-left text-xs ${activeIndex === i ? 'bg-purple-100 font-bold text-purple-800' : 'hover:bg-gray-50'}`}>
                {formatHighlightTime(scene.start)} · {scene.status === '확인 불가' ? '상황 확인 불가' : `${scene.inning}회${scene.half} · ${scene.batter || '타자 정보 없음'}`} {scene.status === '추정' ? '(추정)' : ''}
              </button>)}
            </div>}
          </section>
        </aside>
        <div className="min-w-0 grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(275px,310px)] gap-4 xl:gap-5 items-start xl:h-full xl:min-h-0">
        <section className="min-w-0 rounded-3xl border border-gray-100 bg-white p-3 sm:p-4 shadow-lg shadow-purple-950/5">
          <div className="mb-3 flex items-center justify-between gap-3"><h2 className="font-black text-gray-900">{videoName}</h2><span className="text-xs font-mono text-gray-500">{formatHighlightTime(currentTime)} / {formatHighlightTime(data?.duration_sec ?? 0)}</span></div>
          <YouTubeHighlightPlayer key={selectedId} videoId={selectedId} onTimeUpdate={updateTime} seekSeconds={seekSeconds} seekToken={seekToken}/>
        </section>
        <section className="min-w-0 rounded-3xl border border-gray-100 bg-white p-4 sm:p-5 shadow-lg shadow-purple-950/5 xl:h-full xl:min-h-0 xl:overflow-y-auto xl:overscroll-contain" aria-live="polite" aria-label="현재 장면 상황 스크롤 영역">
          <h2 className="px-1 pt-1 text-sm font-black text-gray-900">현재 장면 상황</h2>
          <div className="mt-3 mb-3 flex flex-wrap items-center gap-2 text-xs" aria-label="영상과 연동된 현재 장면 요약">
            <span className="rounded-full bg-purple-50 px-2.5 py-1 font-bold text-purple-800">현재 장면</span>
            <span className="font-semibold text-gray-700">{activeScene ? `${activeScene.inning}회${activeScene.half} · ${activeScene.batter || '타자 정보 없음'}` : '장면을 확인하고 있어요'}</span>
            {activeScene?.status === '추정' && <span className="rounded-full bg-amber-50 px-2 py-1 font-bold text-amber-800">추정</span>}
          </div>
          {loading && <div className="mt-5 flex items-center gap-2 rounded-xl bg-slate-50 p-4 text-sm text-gray-600"><LoaderCircle className="animate-spin" size={17}/> 장면 데이터 불러오는 중…</div>}
          {sceneError && <div role="alert" className="mt-5 flex items-center gap-2 rounded-xl bg-rose-50 p-4 text-sm text-rose-700"><AlertCircle size={17}/>{sceneError}</div>}
          {!loading && !sceneError && data && <HighlightDetailPanel key={`${selectedId}-${activeIndex}`} scene={activeScene} video={data} onNavigate={onNavigate}/>}
        </section>
        </div>
      </div>
    </div>
  </div>;
}
