import { useEffect, useState } from 'react';

// Keys match the values saved by TeamSelectPage and MY team settings.
const TEAM_ASSETS: Record<string, string> = {
  KIA: 'kia',
  삼성: 'samsung',
  LG: 'lg',
  두산: 'doosan',
  KT: 'kt',
  SSG: 'ssg',
  롯데: 'lotte',
  한화: 'hanwha',
  NC: 'nc',
  키움: 'kiwoom',
};

function getFavoriteTeamAsset(): string | null {
  if (typeof window === 'undefined') return null;
  const favoriteTeam = window.localStorage.getItem('favoriteTeam');
  return favoriteTeam ? TEAM_ASSETS[favoriteTeam] ?? null : null;
}

export interface TeamMascotProps {
  className?: string;
  /** Header uses original logo if no team is selected; other placements use bite mascot. */
  variant?: 'header' | 'bite';
  alt?: string;
}

export function TeamMascot({ className, variant = 'bite', alt }: TeamMascotProps) {
  const [teamAsset, setTeamAsset] = useState<string | null>(getFavoriteTeamAsset);

  useEffect(() => {
    const sync = () => setTeamAsset(getFavoriteTeamAsset());
    window.addEventListener('storage', sync);
    window.addEventListener('yagu:favorite-team-changed', sync);
    return () => {
      window.removeEventListener('storage', sync);
      window.removeEventListener('yagu:favorite-team-changed', sync);
    };
  }, []);

  const imagePath = teamAsset
    ? `/mascots/${teamAsset}.png`
    : variant === 'header'
      ? '/images/yagu-hanip-logo.png'
      : '/images/hanip-bite-mascot.png';

  return (
    <img
      src={imagePath}
      alt={alt ?? (teamAsset ? '선택한 응원팀의 야구한입 캐릭터' : variant === 'header' ? '야구한입 로고' : '')}
      aria-hidden={alt === '' ? true : undefined}
      className={className}
    />
  );
}
