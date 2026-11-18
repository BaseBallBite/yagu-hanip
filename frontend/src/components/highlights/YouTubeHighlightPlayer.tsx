import { useEffect, useRef, useState } from 'react';
import { AlertCircle } from 'lucide-react';

interface YTPlayer {
  getCurrentTime: () => number;
  seekTo: (seconds: number, allowSeekAhead: boolean) => void;
  destroy: () => void;
}
interface YTNamespace {
  Player: new (element: HTMLElement, options: {
    videoId: string;
    playerVars: Record<string, number>;
    events: { onReady: () => void; onError: (event: { data: number }) => void };
  }) => YTPlayer;
}
declare global {
  interface Window {
    YT?: YTNamespace;
    onYouTubeIframeAPIReady?: () => void;
  }
}

let apiPromise: Promise<YTNamespace> | undefined;
function youtubeAPI(): Promise<YTNamespace> {
  if (window.YT?.Player) return Promise.resolve(window.YT);
  if (!apiPromise) {
    apiPromise = new Promise((resolve, reject) => {
      const old = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        old?.();
        if (window.YT?.Player) resolve(window.YT);
        else reject(new Error('YouTube 플레이어를 시작하지 못했습니다.'));
      };
      if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
        const script = document.createElement('script');
        script.src = 'https://www.youtube.com/iframe_api';
        script.onerror = () => reject(new Error('YouTube 플레이어 스크립트를 불러올 수 없습니다.'));
        document.head.appendChild(script);
      }
    }).catch(error => { apiPromise = undefined; throw error; });
  }
  return apiPromise;
}

interface Props {
  videoId: string;
  onTimeUpdate: (seconds: number) => void;
  seekSeconds: number | null;
  seekToken: number;
}
export function YouTubeHighlightPlayer({ videoId, onTimeUpdate, seekSeconds, seekToken }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<YTPlayer | null>(null);
  const currentCallback = useRef(onTimeUpdate);
  const currentSeek = useRef({ seconds: seekSeconds, token: seekToken });
  const [error, setError] = useState('');
  const [ready, setReady] = useState(false);
  currentCallback.current = onTimeUpdate;
  currentSeek.current = { seconds: seekSeconds, token: seekToken };

  useEffect(() => {
    let canceled = false;
    let interval: ReturnType<typeof setInterval> | undefined;
    const mount = document.createElement('div');
    hostRef.current?.appendChild(mount);
    setReady(false);
    setError('');
    youtubeAPI().then(YT => {
      if (canceled) return;
      const player = new YT.Player(mount, {
        videoId,
        playerVars: { playsinline: 1, rel: 0 },
        events: {
          onReady: () => {
            if (canceled) return;
            setReady(true);
            const initial = currentSeek.current.seconds;
            if (initial !== null) player.seekTo(initial, true);
            interval = setInterval(() => {
              try {
                const t = player.getCurrentTime();
                if (Number.isFinite(t)) currentCallback.current(t);
              } catch { /* player may be shutting down */ }
            }, 500);
          },
          onError: () => { if (!canceled) setError('영상을 재생할 수 없습니다. YouTube에서 재생 가능 여부를 확인해 주세요.'); },
        },
      });
      playerRef.current = player;
    }).catch(err => { if (!canceled) setError(err instanceof Error ? err.message : 'YouTube 연결 실패'); });
    return () => {
      canceled = true;
      if (interval) clearInterval(interval);
      try { playerRef.current?.destroy(); } catch { /* player not fully ready */ }
      playerRef.current = null;
      mount.remove();
    };
  }, [videoId]);

  useEffect(() => {
    if (ready && seekSeconds !== null) {
      playerRef.current?.seekTo(seekSeconds, true);
      currentCallback.current(seekSeconds);
    }
  }, [seekSeconds, seekToken, ready]);

  return <div className="space-y-2">
    <div className="relative aspect-video w-full overflow-hidden rounded-2xl bg-slate-950 shadow-lg">
      <div ref={hostRef} className="h-full w-full [&>iframe]:h-full [&>iframe]:w-full" />
      {!ready && !error && <div className="absolute inset-0 grid place-items-center text-sm font-semibold text-white pointer-events-none">YouTube 영상 연결 중…</div>}
    </div>
    {error && <p role="alert" className="flex items-center gap-2 text-sm text-rose-700"><AlertCircle size={16}/>{error}</p>}
  </div>;
}
